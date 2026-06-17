# Jean-Eudes BORNERT - LTSI - 11/03/2026
# Objectif    : Extraction de l'optical flow de la vidéo de l'EEG et ajout d'un tracé représentant l'optical flow
# Fonction    : Interface graphique pour saisir le fichier .edf, la vidéo correspondante et le nom souhaité en sortie. 

# --------------------------------------
# Imports
# --------------------------------------
import tkinter as tk
import os
import sys
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import pyedflib
import threading
import multiprocessing
import time

import back_optical_flow_adder

# --------------------------------------
# Fonctions
# --------------------------------------
def obtenir_chemin_ressource(chemin_relatif, sub_folder=""):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, chemin_relatif)
    if sub_folder:
        return os.path.join(os.path.abspath("."), sub_folder, chemin_relatif)
    return os.path.join(os.path.abspath("."), chemin_relatif)

def browse_edf():
    file_path = filedialog.askopenfilename(title="Choisir un fichier EDF", filetypes=[("EDF files", "*.edf")])
    if file_path: edf_var.set(file_path)

def browse_video():
    file_path = filedialog.askopenfilename(title="Choisir un fichier vidéo", filetypes=[("Video files", "*.mp4")])
    if file_path: video_var.set(file_path)

def _update_log(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)

def log(message):
    root.after(0,lambda:_update_log(message))

def _update_progress(value):
    progress["value"] = value

def set_progress(value):
    root.after(0,lambda:_update_progress(value))

def run_processing(edf_path, video_path, output_name):
    try:
        deb = time.time()
        result = back_optical_flow_adder.process_edf(edf_path, video_path, output_name, log, set_progress)
        
        temps_total = round(time.time() - deb, 2)
        log(f"Temps d'exécution total : {temps_total} secondes")
        
        if result:
            messagebox.showerror("Erreur", result)
        else:
            messagebox.showinfo("Succès", f"Traitement terminé. ")

    except Exception as e:
        log("ECHEC")
        log(str(e))
        messagebox.showerror("Erreur", str(e))

def submit():
    edf_path = edf_var.get()
    video_path = video_var.get()
    output_name = output_var.get()
    
    formats_video = [".mp4"]

    if not edf_path:
        messagebox.showerror("Erreur", "Vous devez fournir un fichier .edf")
        return
    try:
        pyedflib.EdfReader(edf_path)
    except:
        messagebox.showerror("Erreur", "Le fichier .edf n'existe pas")
        return

    if not video_path:
        dossier = os.path.dirname(edf_path)
        base_name = os.path.splitext(os.path.basename(edf_path))[0]
        for ext in formats_video:
            candidate = os.path.join(dossier, base_name + ext)
            if os.path.exists(candidate):
                video_path = candidate
                break
        if not video_path:
            messagebox.showerror("Erreur", f"Aucune vidéo intitulée {base_name}.avi n'est présente dans le dossier")
            return
    else: 
        if not Path(video_path).exists():
            messagebox.showerror("Erreur", "Le chemin d'accès à la vidéo est invalide")
            return
        elif Path(video_path).suffix.lower() not in formats_video:
            messagebox.showerror("Erreur", "Le fichier vidéo DOIT être au format .mp4")
            return

    edf_path = Path(edf_path)
    if not output_name:
        output_name = edf_path.stem + "_optical_flow.edf"

    if os.path.splitext(output_name)[1] != ".edf":
        output_name = os.path.join(edf_path.parent, output_name + ".edf")
    else:
        output_name = os.path.join(edf_path.parent, output_name)
    
    progress["value"] = 0

    thread = threading.Thread(target=run_processing, args=(str(edf_path), str(video_path), str(output_name)))
    thread.start()

# --------------------------------------
# Fenêtre principale
# --------------------------------------
if __name__ == "__main__":
    multiprocessing.freeze_support()
    root = tk.Tk()
    root.title("Optical flow adder")

    chemin_image = obtenir_chemin_ressource("brain_logo.png", "images")
    try:
        img_tk = tk.PhotoImage(file=chemin_image)
        root.iconphoto(True, img_tk)
    except Exception as e:
        pass

    edf_var = tk.StringVar()
    video_var = tk.StringVar()
    output_var = tk.StringVar()

    row_ind = 0
    tk.Label(root, text="Fichier EDF (obligatoire) : ").grid(row=row_ind, column=0, sticky="w")
    tk.Entry(root, textvariable=edf_var, width=50).grid(row=row_ind, column=1)
    tk.Button(root, text="Parcourir", command=browse_edf).grid(row=row_ind, column=2)

    row_ind+=1
    tk.Label(root, text="Fichier vidéo (optionnel*) : ").grid(row=row_ind, column=0, sticky="w")
    tk.Entry(root, textvariable=video_var, width=50).grid(row=row_ind, column=1)
    tk.Button(root, text="Parcourir", command=browse_video).grid(row=row_ind, column=2)

    row_ind+=1
    tk.Label(root, text="* Ne pas préciser le nom du fichier vidéo que si ce dernier a le même nom que le fichier .edf.").grid(row=row_ind, column=0, columnspan=3, sticky="w", pady=(0,10))

    row_ind+=1
    tk.Label(root, text="Nom du fichier de sortie (optionnel**)").grid(row=row_ind, column=0, sticky="w")
    tk.Entry(root, textvariable=output_var, width=50).grid(row=row_ind, column=1)

    row_ind+=1
    tk.Label(root, text="** Si vous ne précisez rien, le fichier sera localisé au même endroit. Attention à l'écrasement.", justify="left").grid(row=row_ind, column=0, columnspan=3, sticky="w", pady=(0,10))

    row_ind+=1
    warning_label = tk.Label(root, 
        text="ATTENTION : la vidéo doit être optimisée en amont :\n- Format : .mp4 (recommandé) ou .avi\n- Noir et Blanc\n- Largeur maximale de 320 pixels",
        fg="red", justify="left", font=("Helvetica", 9, "bold"))
    warning_label.grid(row=row_ind, column=0, columnspan=3, sticky="w", pady=(5,10))

    row_ind+=1
    tk.Button(root, text="Valider", command=submit, bg="green", fg="white").grid(row=row_ind, column=0, columnspan=3, sticky="n")

    row_ind += 1
    log_frame = tk.Frame(root)
    log_frame.grid(row=row_ind, column=0, columnspan=3, pady=10)

    scrollbar = tk.Scrollbar(log_frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    log_box = tk.Text(log_frame, height=10, width=70, yscrollcommand=scrollbar.set)
    log_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar.config(command=log_box.yview)

    row_ind += 1
    progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
    progress.grid(row=row_ind, column=0, columnspan=3, pady=5)

    root.mainloop()