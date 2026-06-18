import os
import sys
import glob
import shutil
import ffmpeg
from fractions import Fraction
import concurrent.futures

_log_callback_externe = None

def set_log_callback(callback):
    global _log_callback_externe
    _log_callback_externe = callback

def log(message):
    if _log_callback_externe:
        _log_callback_externe(message)
    else:
        print(message)

def obtenir_chemin_ressource(chemin_relatif, sub_folder=""):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, chemin_relatif)
    if sub_folder:
        return os.path.join(os.path.abspath("."), sub_folder, chemin_relatif)
    return os.path.join(os.path.abspath("."), chemin_relatif)

def evaluer_fps(fps_str):
    try:
        fps = float(Fraction(fps_str))
        if fps > 60:
            log(f"FPS suspect ({fps_str} = {fps:.1f})")
            return 25.0
        return max(1.0, fps)
    except Exception:
        log(f"FPS illisible ({fps_str})")
        return 25.0


def obtenir_proprietes_video(chemin_video, chemin_ffmpeg):
    try:
        chemin_ffprobe = chemin_ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
        log(chemin_video)
        probe = ffmpeg.probe(chemin_video.replace('\\', '/'), cmd=chemin_ffprobe)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)

        pix_fmt = video_stream.get('pix_fmt', 'yuv420p')
        if pix_fmt == 'yuvj420p':
            pix_fmt = 'yuv420p'

        fps_str = video_stream.get('r_frame_rate', '25/1')
        fps_value = evaluer_fps(fps_str)
        duree_reelle_sec = float(probe['format'].get('duration', 0))

        props = {
            'width': video_stream['width'],
            'height': video_stream['height'],
            'fps_str': fps_str,
            'fps_value': fps_value,
            'pix_fmt': pix_fmt,
            'has_audio': audio_stream is not None,
            'duree_reelle_sec': duree_reelle_sec,
        }
        log(f"  FPS : {fps_str} → {fps_value:.3f} fps | Durée réelle : {duree_reelle_sec:.3f} s")

        if props['has_audio']:
            props['sample_rate'] = audio_stream.get('sample_rate', '44100')
            props['channels'] = audio_stream.get('channels', 2)

        return props
    except Exception as e:
        log(f"Erreur ffprobe sur {chemin_video} : {e}")
        return None


def obtenir_duree(chemin_video, chemin_ffmpeg):
    try:
        chemin_ffprobe = chemin_ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
        probe = ffmpeg.probe(chemin_video.replace('\\', '/'), cmd=chemin_ffprobe)
        return float(probe['format'].get('duration', 0))
    except Exception as e:
        log(f"  Erreur ffprobe durée {chemin_video} : {e}")
        return None


def normaliser_pts(chemin_entree, chemin_sortie, props, chemin_ffmpeg):
    try:
        kwargs = {
            'c': 'copy',
            'video_track_timescale': 90000
        }
        
        kwargs['bsf:v'] = 'setts=ts=TS-STARTPTS'
        if props.get('has_audio'):
            kwargs['bsf:a'] = 'setts=ts=TS-STARTPTS'

        (
            ffmpeg
            .input(chemin_entree)
            .output(chemin_sortie, **kwargs)
            .run(cmd=chemin_ffmpeg, overwrite_output=True, quiet=True)
        )
        return True
    except ffmpeg.Error as e:
        log(f"  Erreur normalisation PTS : {chemin_entree}")
        if e.stderr:
            log(e.stderr.decode('utf-8', errors='ignore'))
        return False


def generer_video_noire(chemin_sortie, duree_ms, props, chemin_ffmpeg):
    duree_sec = duree_ms / 1000.0
    fps = props['fps_value']
    nb_frames = max(1, round(duree_sec * fps))
    duree_reelle_sec = nb_frames / fps

    log(f"  → Vidéo noire : {duree_ms} ms → {nb_frames} frames à {fps:.3f} fps = {duree_reelle_sec*1000:.1f} ms")

    try:
        v = ffmpeg.input(
            f"color=c=black:s={props['width']}x{props['height']}:r={fps}",
            format='lavfi', t=duree_reelle_sec
        )
        kwargs = {
            'vcodec': 'libx264', 'preset': 'ultrafast',
            'tune': 'stillimage', 'crf': 30, 'pix_fmt': props['pix_fmt'],
            'video_track_timescale': 90000
        }
        if props['has_audio']:
            sr = props.get('sample_rate', '44100')
            ch = 'stereo' if props.get('channels', 2) == 2 else 'mono'
            a = ffmpeg.input(f"anullsrc=r={sr}:cl={ch}", format='lavfi', t=duree_reelle_sec)
            kwargs.update({'acodec': 'aac', 'ar': sr})
            ffmpeg.output(v, a, chemin_sortie, **kwargs).run(cmd=chemin_ffmpeg, overwrite_output=True, quiet=True)
        else:
            ffmpeg.output(v, chemin_sortie, **kwargs).run(cmd=chemin_ffmpeg, overwrite_output=True, quiet=True)

        return duree_reelle_sec
    except ffmpeg.Error as e:
        log(f"  Erreur création vidéo noire.")
        if e.stderr:
            log(e.stderr.decode('utf-8', errors='ignore'))
        return None

def verifier_presence_ffmpeg(chemin_ffmpeg):
    chemin_ffprobe = chemin_ffmpeg.replace('ffmpeg.exe', 'ffprobe.exe')
    
    # Vérification de ffmpeg.exe
    if not os.path.exists(chemin_ffmpeg):
        log(f"\nERREUR : L'exécutable ffmpeg est introuvable. ")
        log(f"   Chemin cherché : {os.path.abspath(chemin_ffmpeg)}")
        return False
        
    # Vérification de ffprobe.exe
    if not os.path.exists(chemin_ffprobe):
        log(f"\nERREUR : L'exécutable ffprobe est introuvable. ")
        log(f"   Chemin cherché : {os.path.abspath(chemin_ffprobe)}")
        return False
        
    return True

def analyser_videos_vwr(chemin_vwr, fichier_sortie=None, log_callback=None):

    if log_callback:
        set_log_callback(log_callback)

    if not os.path.exists(chemin_vwr):
        log(f"ERREUR : Le fichier {chemin_vwr} est introuvable.")
        return False

    chemin_ffmpeg = obtenir_chemin_ressource(os.path.join('ffmpeg', 'ffmpeg.exe'))

    if not verifier_presence_ffmpeg(chemin_ffmpeg):
        log("ERREUR : FFmpeg est introuvable.")
        return False

    dossier_vwr = os.path.dirname(chemin_vwr)
    nom_base_vwr = os.path.splitext(os.path.basename(chemin_vwr))[0]
    
    if fichier_sortie is None:
        fichier_sortie = f"{nom_base_vwr}.mp4"
        
    dossier_tmp = os.path.join(dossier_vwr, "_tmp_assembly")
    os.makedirs(dossier_tmp, exist_ok=True)

    try:

        log(f"Démarrage de l'analyse pour : {nom_base_vwr}.vwr")

        # 1. Lecture du fichier VWR
        videos = []
        try:
            with open(chemin_vwr, 'rb') as f:
                f.seek(0x0168)
                adresse_videos = int.from_bytes(f.read(3), byteorder='little')
                f.seek(adresse_videos)
                separateur_attendu = b'\x00\x00\x00\xff\xff\xff\xff'

                while True:
                    donnees_video = f.read(9)
                    if len(donnees_video) < 9:
                        break
                    numero_video = donnees_video[8]
                    if numero_video == 255:
                        break

                    debut_ms = int.from_bytes(donnees_video[0:4], byteorder='little')
                    duree_ms = int.from_bytes(donnees_video[4:8], byteorder='little')
                    videos.append({'numero': numero_video, 'debut_ms': debut_ms, 'duree_ms': duree_ms})

                    if f.read(7) != separateur_attendu:
                        break
        except Exception as e:
            log(f"Erreur de lecture du VWR : {e}")
            return False

        if not videos:
            log("Erreur : Aucune entrée vidéo dans le VWR.")
            return False

        log(f"\n{len(videos)} segment(s) trouvé(s) dans le VWR.")

        # 2. Association fichiers physiques
        fichiers_physiques = {}
        for v in videos:
            numero = v['numero']
            trouves = glob.glob(os.path.join(dossier_vwr, f"{nom_base_vwr}_{numero}.*"))
            if trouves:
                fichiers_physiques[numero] = trouves[0]
            else:
                log(f"Erreur : Vidéo _{numero} introuvable. ")
                return False

        # 3. Propriétés du premier segment
        log("\nAnalyse du premier segment...")
        props_video = obtenir_proprietes_video(fichiers_physiques[videos[0]['numero']], chemin_ffmpeg)
        if not props_video:
            return False

        # 4. Normalisation PTS de chaque segment source
        log("\n--- Normalisation des PTS (en parallèle) ---")
        fichiers_normalises = {}

        def process_segment(v):
            num = v['numero']
            source = fichiers_physiques[num]
            dest = os.path.join(dossier_tmp, f"norm_{num}.mp4")
            succes = normaliser_pts(source, dest, props_video, chemin_ffmpeg)
            return num, dest, succes

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_segment, v) for v in videos]
            for future in concurrent.futures.as_completed(futures):
                num, dest, succes = future.result()
                if not succes:
                    log(f"Erreur sur le segment {num}")
                    return False
                fichiers_normalises[num] = dest
                log(f"  ✓ Segment _{num} terminé.")
        
        # 5. Construction de la liste avec gaps
        log("\n--- Création de la vidéo noire Master ---")
        chemin_noir_master = os.path.join(dossier_tmp, "noir_master.mp4")

        # 6. Calcul du plus grand gap
        max_gap_ms = 0
        temps_virtuel_ms = 0
        for v in videos:
            gap_ms = v['debut_ms'] - temps_virtuel_ms
            if gap_ms > max_gap_ms:
                max_gap_ms = gap_ms
            temps_virtuel_ms = v['debut_ms'] + v['duree_ms']

        duree_master_noire_ms = max(1000, max_gap_ms + 500)
        
        log(f"Plus long gap détecté : {max_gap_ms} ms")
        
        # 7. Génération du gap
        generer_video_noire(chemin_noir_master, duree_master_noire_ms, props_video, chemin_ffmpeg)

        segments = []
        temps_courant_ms = 0

        log("\n--- Calcul des gaps ---")
        for v in videos:
            numero = v['numero']
            debut_attendu = v['debut_ms']
            duree_video_ms = v['duree_ms']
            gap_ms = debut_attendu - temps_courant_ms

            if gap_ms > 0:
                duree_reelle_sec = gap_ms / 1000.0
                log(f"Ajout d'un segment noir de {duree_reelle_sec:.3f} secondes (avant segment _{numero}). ")
                segments.append((chemin_noir_master, duree_reelle_sec, True))
            elif gap_ms < 0:
                log(f"Chevauchement de {abs(gap_ms)} ms sur segment _{numero}.")
                return False

            duree_norm_sec = obtenir_duree(fichiers_normalises[numero], chemin_ffmpeg)
            if duree_norm_sec is None:
                return False
            segments.append((fichiers_normalises[numero], duree_norm_sec, False))
            temps_courant_ms = debut_attendu + duree_video_ms

        # 6. Fichier ffconcat
        fichier_liste_txt = os.path.join(dossier_tmp, "liste_ffmpeg.txt")
        with open(fichier_liste_txt, 'w', encoding='utf-8') as f_list:
            f_list.write("ffconcat version 1.0\n")
            for chemin, duree_sec, is_gap in segments:
                chemin_safe = chemin.replace('\\', '/')
                f_list.write(f"file '{chemin_safe}'\n")
                if is_gap:
                    f_list.write("inpoint 0\n")
                    f_list.write(f"outpoint {duree_sec:.6f}\n")
                else:
                    f_list.write(f"duration {duree_sec:.6f}\n")

        # 7. Assemblage final
        chemin_sortie_mp4 = os.path.join(dossier_vwr, fichier_sortie)

        log("\n--- Assemblage final ---")
        try:
            log("Fusion en MP4 en cours (Pour plus d'information sur la progression, regardez le terminal)...")
            (
                ffmpeg
                .input(fichier_liste_txt, format='concat', safe=0)
                .output(chemin_sortie_mp4, c='copy')
                .run(cmd=chemin_ffmpeg, overwrite_output=True, quiet=False)
            )
            log(f"Succès : Vidéo disponible : {chemin_sortie_mp4}")
            return True

        except ffmpeg.Error as e:
            log("Erreur lors de la fusion.")
            if e.stderr:
                log(e.stderr.decode('utf-8', errors='ignore'))
            return False

    finally:
        log("Nettoyage des fichiers temporaires...")
        if os.path.exists(dossier_tmp):
            shutil.rmtree(dossier_tmp)
        log("Traitement terminé. ")