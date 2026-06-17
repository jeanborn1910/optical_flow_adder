# Jean-Eudes BORNERT - LTSI - 25/03/2026
# Objectif    : Transformation de vidéos au format mp4 standard ou mp4 optimisé pour l'optical flow
# Fonction    : Interface graphique pour saisir les fichiers vidéo et choisir les traitements. 

# --------------------------------------
# Imports
# --------------------------------------
import tkinter as tk
import os
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import datetime
from tkcalendar import DateEntry
import ffmpeg

import back_convert_video

# --------------------------------------
# Fonctions
# --------------------------------------
def verifier_format(*args):
    chemins = video_var.get().split(';')
    
    if not chemins or not chemins[0]:
        cadre_date_heure.grid_remove()
        assemble_file.grid_remove()
        mp4_file.config(state="normal")
        return
        
    contient_mpeg = any(c.lower().endswith(('.mpeg', '.mpg', '.mpe')) for c in chemins)
    
    if len(chemins) > 1:
        if contient_mpeg:
            messagebox.showerror(
                "Action impossible", 
                "Il n'est pas possible de traiter plusieurs fichiers MPEG en même temps.\n\n"
                "Veuillez convertir chaque fichier en mp4, puis les assembler."
            )
            root.after(10, lambda: video_var.set(""))
            return
        
        cadre_date_heure.grid_remove()
        assemble_file.grid(row=row_assemble, column=0, columnspan=3, sticky="w", padx=5)
        bool_assemble_file.set(1)
        assemble_file.config(state="disabled")
        
        mp4_file.config(state="normal")
        return

    assemble_file.grid_remove()
    bool_assemble_file.set(0)
    
    nom_fichier = chemins[0].lower()
    
    if nom_fichier.endswith(('.mpeg', '.mpg', '.mpe')):
        cadre_date_heure.grid(row=row_date_heure, column=0, columnspan=3, pady=10, sticky="w")
        bool_mp4_file.set(1)
        mp4_file.config(state="disabled")
    elif nom_fichier.endswith(('.mp4')):
        bool_mp4_file.set(0)
        cadre_date_heure.grid_remove()
        mp4_file.config(state="disabled")
    else:
        cadre_date_heure.grid_remove()
        mp4_file.config(state="normal")

def obtenir_date_formatee():
    date_sel = calendrier.get_date()
    h = spin_heures.get().zfill(2)
    m = spin_minutes.get().zfill(2)
    s = spin_secondes.get().zfill(2)
    return f"{date_sel.strftime('%Y-%m-%d')}T{h}:{m}:{s}"

def browse_video():
    file_paths = filedialog.askopenfilenames(
        title="Choisir un ou plusieurs fichiers vidéo",
        filetypes=[("Video files", "*.avi *.mp4 *.mov *.mkv *.mpeg *.mpg *.mpe")]
    )
    if file_paths:
        video_var.set(";".join(file_paths))

def log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    root.update_idletasks()

def set_progress(value):
    progress["value"] = value
    root.update_idletasks()

def extraire_date_creation(input_file):
    try:
        chemin_ffprobe = back_convert_video.obtenir_chemin_ressource("ffprobe.exe", "ffmpeg")
        infos = ffmpeg.probe(input_file, cmd=chemin_ffprobe)
        
        tags = infos.get('format', {}).get('tags', {})
        date_brute = tags.get('creation_time')
        
        if not date_brute:
            for stream in infos.get('streams', []):
                if stream.get('codec_type') == 'video':
                    date_brute = stream.get('tags', {}).get('creation_time')
                    if date_brute:
                        break
                        
        if date_brute:
            date_propre = date_brute.split('.')[0].replace('T', ' ').replace('Z', '')
            return date_propre
            
    except Exception as e:
        print(f"Impossible d'extraire la date : {e}")
        
    return None

def run_combined_processing(video_paths_str, output_base_name, date_str, do_mp4, do_of):
    try:
        fichiers_entree = video_paths_str.split(';')
        video_p = Path(fichiers_entree[0])
        parent_dir = video_p.parent
        fichier_source = fichiers_entree[0]
        
        base_name = output_base_name if output_base_name else video_p.stem

        if not date_str:
            date_extraite = extraire_date_creation(fichier_source)
            if date_extraite:
                date_str = date_extraite
                log(f"Date extraite de la source : {date_str}")
            else:
                log("Aucune date trouvée dans la vidéo source.")

        if len(fichiers_entree) > 1:
            log("Plusieurs fichiers détectés. Démarrage de l'assemblage...")

            ext = video_p.suffix
            out_assemble_name = f"{base_name}_assemble{ext}"
            chemin_assemble = os.path.join(parent_dir, out_assemble_name)
            
            back_convert_video.assembler_videos(fichiers_entree, chemin_assemble, log, set_progress)
            
            fichier_source = chemin_assemble
            base_name = f"{base_name}_assemble"
            set_progress(0)

        if do_mp4:
            log("Démarrage de la conversion MP4 de visionnage (optimisée)...")
            out_mp4 = base_name if output_base_name else f"{base_name}_converted"

            back_convert_video.convert_mpeg_to_mp4(
                fichier_source, 
                out_mp4, 
                date_str, 
                log, 
                set_progress
            )
            log("Conversion MP4 terminée.")
            nom_mp4_final = out_mp4 if out_mp4.lower().endswith(".mp4") else f"{out_mp4}.mp4"
            
            fichier_source = os.path.join(parent_dir, nom_mp4_final)
            set_progress(0)
            
            fichier_source = os.path.join(parent_dir, nom_mp4_final)
            set_progress(0)

        if do_of:
            log("Conversion de la vidéo en vu du flot optique...")
            
            out_of_name = f"{base_name}_of.mp4"
            out_of_path = os.path.join(parent_dir, out_of_name)
            
            back_convert_video.convert_for_optical_flow(
                fichier_source, 
                out_of_path, 
                date_str, 
                log, 
                set_progress,
                largeur_cible=320
            )
            log("Conversion au format MP4 pour le flot optique terminée.")
        
        messagebox.showinfo("Succès", "Tous les traitements sont terminés.")
        set_progress(0)

    except Exception as e:
        log(f"Erreur : {str(e)}")
        messagebox.showerror("Erreur", str(e))
        set_progress(0)

def submit():
    video_paths_str = video_var.get()
    output_name = output_var.get()
    
    do_mp4 = bool_mp4_file.get()
    do_of = bool_of_file.get()

    if not video_paths_str:
        messagebox.showerror("Erreur", "Le chemin d'accès à la/les vidéo(s) est invalide.")
        return

    chemins = video_paths_str.split(';')
    for c in chemins:
        if not Path(c).exists():
            messagebox.showerror("Erreur", f"Fichier introuvable : {c}")
            return

    if len(chemins) > 1:
        extensions = [Path(c).suffix.lower() for c in chemins]
        if len(set(extensions)) > 1:
            messagebox.showerror(
                "Erreur de format", 
                "Tous les fichiers sélectionnés doivent avoir la même extension pour être assemblés proprement."
            )
            return

    if len(chemins) == 1 and not do_mp4 and not do_of:
        messagebox.showerror("Erreur", "Sélectionnez au moins une conversion à réaliser.")
        return

    date_iso = ""
    if len(chemins) == 1 and chemins[0].lower().endswith(('.mpeg', '.mpg', '.mpe')):
        date_iso = obtenir_date_formatee()

    progress["value"] = 0
    thread = threading.Thread(
        target=run_combined_processing,
        args=(video_paths_str, output_name, date_iso, do_mp4, do_of)
    )
    thread.daemon = True
    thread.start()

# --------------------------------------
# Fenêtre principale
# --------------------------------------
root = tk.Tk()
root.title("Video converter for flot optique")
chemin_image = back_convert_video.obtenir_chemin_ressource("video_logo.png", "images")
try:
    img_tk = tk.PhotoImage(file=chemin_image)
    root.iconphoto(True, img_tk)
except Exception:
    pass

video_var = tk.StringVar()
output_var = tk.StringVar()
bool_assemble_file = tk.IntVar()
bool_mp4_file = tk.IntVar()
bool_of_file = tk.IntVar()

row_ind = 0
tk.Label(root, text="Fichier(s) vidéo à traiter :").grid(row=row_ind, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=video_var, width=50).grid(row=row_ind, column=1, padx=5)
tk.Button(root, text="Parcourir", command=browse_video).grid(row=row_ind, column=2, padx=5)

row_ind += 1
tk.Label(root, text="Nom de base en sortie (optionnel*) :").grid(row=row_ind, column=0, sticky="w", padx=5, pady=5)
tk.Entry(root, textvariable=output_var, width=50).grid(row=row_ind, column=1, padx=5)

row_ind += 1
tk.Label(root, text="* Si vide, le nom d'entrée sera utilisé avec '_assemble', '_converted' ou '_of' à la fin.", justify="left").grid(row=row_ind, column=0, columnspan=3, sticky="w", pady=(0,10), padx=5)

row_ind += 1
row_date_heure = row_ind
cadre_date_heure = tk.Frame(root)
tk.Label(cadre_date_heure, text="Date/Heure du MPEG :", font=('Arial', 9, 'bold')).pack(side=tk.LEFT, padx=5)
calendrier = DateEntry(cadre_date_heure, width=12, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy')
calendrier.pack(side=tk.LEFT, padx=5)
spin_heures = ttk.Spinbox(cadre_date_heure, from_=0, to=23, width=3, format="%02.0f", wrap=True)
spin_heures.pack(side=tk.LEFT)
tk.Label(cadre_date_heure, text=":").pack(side=tk.LEFT)
spin_minutes = ttk.Spinbox(cadre_date_heure, from_=0, to=59, width=3, format="%02.0f", wrap=True)
spin_minutes.pack(side=tk.LEFT)
tk.Label(cadre_date_heure, text=":").pack(side=tk.LEFT)
spin_secondes = ttk.Spinbox(cadre_date_heure, from_=0, to=59, width=3, format="%02.0f", wrap=True)
spin_secondes.pack(side=tk.LEFT)

row_ind += 1
row_assemble = row_ind
assemble_file = tk.Checkbutton(root, text="Assembler les fichiers vidéo en une longue vidéo", variable=bool_assemble_file)

row_ind += 1
mp4_file = tk.Checkbutton(root, text="Convertir le fichier en .mp4", variable=bool_mp4_file)
mp4_file.grid(row=row_ind, column=0, columnspan=3, sticky="w", padx=5)

row_ind += 1
of_file = tk.Checkbutton(
    root, 
    text="Convertir le fichier pour le flot optique (attention, le fichier peut être volumineux,\n assurez-vous d'avoir le stockage nécessaire)", 
    variable=bool_of_file,
    justify="left"
)
of_file.grid(row=row_ind, column=0, columnspan=3, sticky="w", padx=5)

row_ind+=1
tk.Button(root, text="Valider", command=submit, bg="green", fg="white").grid(row=row_ind, column=0, columnspan=3, sticky="n", pady=5)

# Log
row_ind += 1
log_frame = tk.Frame(root)
log_frame.grid(row=row_ind, column=0, columnspan=3, pady=10)

scrollbar = tk.Scrollbar(log_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

log_box = tk.Text(log_frame, height=10, width=70, yscrollcommand=scrollbar.set)
log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

row_ind += 1
progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress.grid(row=row_ind, column=0, columnspan=3, pady=5)

now = datetime.datetime.now()
spin_heures.set(now.hour)
spin_minutes.set(now.minute)
spin_secondes.set(now.second)

video_var.trace_add("write", verifier_format)

root.mainloop()