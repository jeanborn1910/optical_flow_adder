# Jean-Eudes BORNERT - LTSI - 25/03/2026
# Objectif    : Back end pour la conversion des vidéos en mp4 standard ou mp4 pour of, et assemblage
# Fonction    : Code de base permettant de traiter les vidéos
# Entrée      : fichiers vidéos (.avi, .mp4, etc.)
# Sortie      : vidéos traitées selon le besoin (assemblées, mp4 standard, mp4 optical flow)

# --------------------------------------
# Imports
# --------------------------------------
import ffmpeg
import os
import sys
from datetime import datetime, timedelta

# --------------------------------------
# Obtenir le chemin des ressources
# --------------------------------------
def obtenir_chemin_ressource(chemin_relatif, sub_folder=""):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, chemin_relatif)
    if sub_folder:
        return os.path.join(os.path.abspath("."), sub_folder, chemin_relatif)
    return os.path.join(os.path.abspath("."), chemin_relatif)

# --------------------------------------
# Dates os
# --------------------------------------
def modifier_dates_os(chemin_fichier, date_iso):
    if not date_iso:
        return
        
    try:
        date_str = date_iso.replace('T', ' ').split('.')[0]
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        timestamp = dt.timestamp()
        
        os.utime(chemin_fichier, (timestamp, timestamp))
        
        chemin_propre = os.path.abspath(chemin_fichier).replace("'", "''")
        commande = f'powershell -Command "(Get-Item \'{chemin_propre}\').CreationTime = \'{date_str}\'"'
        os.system(commande)
        
    except Exception as e:
        print(f"Information : Impossible de modifier les dates de l'OS : {e}")

# --------------------------------------
# Fonctions pour l'assemblage et continuité
# --------------------------------------
def analyser_video(chemin_fichier, chemin_ffprobe):
    try:
        metadonnees = ffmpeg.probe(chemin_fichier, cmd=chemin_ffprobe)
        format_info = metadonnees.get('format', {})
        
        # Date
        date_brute = format_info.get('tags', {}).get('creation_time')
        date_obj = datetime.min
        if date_brute:
            date_propre = date_brute[:19].replace('T', ' ')
            try:
                date_obj = datetime.strptime(date_propre, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
        
        duree_brute = float(format_info.get('duration', 0))
        duree_td = timedelta(seconds=duree_brute)
        
        return {
            'fichier': chemin_fichier,
            'debut': date_obj,
            'duree': duree_td,
            'date_brute': date_brute
        }
    except Exception as e:
        raise ValueError(f"Erreur d'analyse pour {chemin_fichier} : {e}")

def assembler_videos(fichiers_entree, fichier_sortie, log, set_progress, tolerance_secondes=2.0):
    log("Analyse des métadonnées en cours...")
    chemin_ffprobe = obtenir_chemin_ressource("ffprobe.exe", "ffmpeg")
    set_progress(10)
    
    videos_data = []
    for f in fichiers_entree:
        data = analyser_video(f, chemin_ffprobe)
        if data:
            videos_data.append(data)

    # Tri chronologique basé sur la date de début
    videos_data.sort(key=lambda x: x['debut'])

    log("Ordre d'assemblage défini :")
    for v in videos_data:
        log(f"- {os.path.basename(v['fichier'])}")

    # Vérification de la continuité
    log("Vérification de la continuité des vidéos...")
    set_progress(30)
    videos_valides = True

    for i in range(len(videos_data) - 1):
        vid_actuelle = videos_data[i]
        vid_suivante = videos_data[i+1]
        
        fin_theorique = vid_actuelle['debut'] + vid_actuelle['duree']
        debut_reel_suivant = vid_suivante['debut']
        
        ecart = abs((debut_reel_suivant - fin_theorique).total_seconds())
        
        if ecart > tolerance_secondes:
            log(f"Discontinuité détectée : '{os.path.basename(vid_actuelle['fichier'])}' et '{os.path.basename(vid_suivante['fichier'])}'")
            log(f"  Écart constaté : {ecart:.2f} s (Tolérance: {tolerance_secondes}s)")
            videos_valides = False

    if not videos_valides:
        raise ValueError("Échec de l'assemblage : les vidéos ne sont pas continues (écart trop grand).")

    # Préparation et Assemblage
    log("Préparation de l'assemblage des vidéos...")
    set_progress(50)
    
    dossier_sortie = os.path.dirname(fichier_sortie)
    fichier_texte = os.path.join(dossier_sortie, "liste_videos_temp.txt")
    
    with open(fichier_texte, "w", encoding="utf-8") as f:
        for v in videos_data:
            chemin_echappe = v['fichier'].replace('\\', '/')
            f.write(f"file '{chemin_echappe}'\n")

    try:
        chemin_ffmpeg = obtenir_chemin_ressource("ffmpeg.exe", "ffmpeg")
        options_sortie = {'c': 'copy'}
        
        # Réinjection de la date de la première vidéo
        date_premiere = videos_data[0].get('date_brute')
        if date_premiere:
            options_sortie['metadata'] = f'creation_time={date_premiere}'

        log("Assemblage en cours via FFmpeg...")
        log("(la barre de chargement n'évoluera pas, voir les informations du terminal)")
        (
            ffmpeg
            .input(fichier_texte, format='concat', safe=0)
            .output(fichier_sortie, **options_sortie)
            .run(cmd=chemin_ffmpeg, overwrite_output=True)
        )
        log(f"Fichier assemblé : {os.path.basename(fichier_sortie)}")
        set_progress(100)

    except ffmpeg.Error as e:
        erreur_msg = e.stderr.decode('utf8') if e.stderr else 'Inconnue'
        raise ValueError(f"Erreur FFmpeg lors de l'assemblage : {erreur_msg}")
    finally:
        if os.path.exists(fichier_texte):
            os.remove(fichier_texte)

# --------------------------------------
# Fonction pour optical flow
# --------------------------------------
def convert_for_optical_flow(input_path, output_path, date_heure_debut, log, set_progress, largeur_cible=320):
    log("(la barre de chargement n'évoluera pas, voir les informations du terminal)")
    chemin_ffmpeg = obtenir_chemin_ressource("ffmpeg.exe", "ffmpeg")
    
    set_progress(50) 
    
    output_kwargs = {
        'vf': f'scale={largeur_cible}:-2',
        'vcodec': 'libx264',
        'preset': 'ultrafast',
        'tune': 'fastdecode',
        'pix_fmt': 'gray',
        'crf': 23,
        'g': 25,
        'keyint_min': 25
    }
    
    if date_heure_debut:
        log(f"Injection de la date dans le flot optique : {date_heure_debut.replace('T', ' ')}")
        output_kwargs['metadata'] = f'creation_time={date_heure_debut}'
    
    try:
        (
            ffmpeg
            .input(input_path)
            .output(output_path, **output_kwargs)
            .run(cmd=chemin_ffmpeg, overwrite_output=True)
        )

        modifier_dates_os(output_path, date_heure_debut)    

        set_progress(100)
        log(f"Fichier sauvegardé : {os.path.basename(output_path)}")
        
    except ffmpeg.Error as e:
        set_progress(0)
        erreur = e.stderr.decode('utf8') if e.stderr else 'Erreur'
        raise ValueError(f"Erreur lors de la création de la vidéo de flot optique : {erreur}")

# --------------------------------------
# Fonction pour fichiers en mp4
# --------------------------------------
def convert_mpeg_to_mp4(input_file, output_file_name, date_heure_debut, log, set_progress):
    path = os.path.dirname(input_file)
    
    if not output_file_name.lower().endswith('.mp4'):
        output_file_name += ".mp4"
    
    full_output_path = os.path.normpath(os.path.join(path, output_file_name))
    chemin_ffmpeg = obtenir_chemin_ressource("ffmpeg.exe", "ffmpeg")
    
    set_progress(50)
    log("Merci de patienter, cette étape peut prendre du temps... ")
    log("(la barre de chargement n'évoluera pas, voir les informations du terminal)")
    
    try:
        # Paramètres pour une vidéo fluide, rapide à lire, et IGNORANT les erreurs MPEG
        output_kwargs = {
            'vcodec': 'libx264',
            'preset': 'fast',
            'crf': 23,
            'g': 25,
            'keyint_min': 25,
            'an': None,           # Supprime la piste audio corrompue
            'fflags': '+genpts'   # <-- BOUCLIER 1 : Régénère les timestamps (DTS out of order)
        }
        
        if date_heure_debut != "":
            log(f"Injection de la date : {date_heure_debut.replace('T', ' ')}")
            output_kwargs['metadata'] = f'creation_time={date_heure_debut}'

        (
            ffmpeg
            # <-- BOUCLIER 2 : Ignore les erreurs de lecture (headers mp2 manquants) dès l'entrée
            .input(input_file, err_detect='ignore_err') 
            .output(full_output_path, **output_kwargs)
            .run(cmd=chemin_ffmpeg, overwrite_output=True)
        )
        
        # Mise à jour des dates Windows
        modifier_dates_os(full_output_path, date_heure_debut)
        
        set_progress(100)
    
    except ffmpeg.Error as e:
        set_progress(0)
        raise ValueError("Erreur FFmpeg détectée : " + (e.stderr.decode() if e.stderr else "Erreur inconnue"))