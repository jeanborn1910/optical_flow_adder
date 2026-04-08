# Jean-Eudes BORNERT - LTSI - 30/03/2026
# Objectif    : Transformation de vidéos au format avi optimisé pour l'optical flow pour une zone spécifique
# Fonction    : Extraire l'intégralité de la vidéo dans la zone définie par l'utilisateur

# --------------------------------------
# Imports
# --------------------------------------
import tkinter as tk
from tkinter import messagebox
import ffmpeg
import os
import sys
import datetime

# --------------------------------------
# Fonctions
# --------------------------------------
def obtenir_chemin_ressource(chemin_relatif, sub_folder=""):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, chemin_relatif)
    if sub_folder:
        return os.path.join(os.path.abspath("."), sub_folder, chemin_relatif)
    return os.path.join(os.path.abspath("."), chemin_relatif)

def process_video(input_video_path, coords, on_complete=None):
    """
    Interface pour afficher le statut et lancer FFmpeg.
    coords contient (x_min, y_min, x_max, y_max)
    """

    x_min, y_min, x_max, y_max = coords
    width = x_max - x_min
    height = y_max - y_min
    
    video_dir = os.path.dirname(input_video_path)
    
    base_name = os.path.splitext(os.path.basename(input_video_path))[0]
    
    timestamp = os.path.getmtime(input_video_path)
    date_heure = datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d_%H-%M-%S")
    
    output_name = f"{base_name}_{date_heure}_zone.avi"
    output_video_path = os.path.join(video_dir, output_name)

    proc_window = tk.Toplevel()
    proc_window.title("Traitement vidéo")
    proc_window.geometry("300x150")
    proc_window.attributes('-topmost', True)
    scale_max = 320
    chemin_ffmpeg = obtenir_chemin_ressource("ffmpeg.exe", "ffmpeg")

    status_label = tk.Label(proc_window, text="Traitement en cours avec FFmpeg...\nVeuillez patienter. \n(Pour voir l'évolution, regarder les informations du terminal)", pady=20)
    status_label.pack(expand=True)
    

    proc_window.update()
    
    
    def fermer_et_reset():
        if on_complete:
            on_complete()
        proc_window.destroy()

    try:
        stream = ffmpeg.input(input_video_path)
        stream = ffmpeg.crop(stream, x_min, y_min, width, height)
        stream = ffmpeg.filter(stream, 'scale', scale_max, -1)
        stream = ffmpeg.filter(stream, 'format', 'gray')
        stream = ffmpeg.output(stream, output_video_path, an=None)
        ffmpeg.run(stream, cmd=chemin_ffmpeg, overwrite_output=True)
        
        status_label.config(text=f"Traitement terminé. \nSauvegardé sous :\n{os.path.basename(output_video_path)}")
        
    except ffmpeg.Error as e:
        err_msg = e.stderr.decode('utf-8') if e.stderr else "Erreur inconnue"
        status_label.config(text="Erreur FFmpeg.", fg="red")
        messagebox.showerror("Erreur FFmpeg", f"Détails :\n{err_msg}", parent=proc_window)
    
    except FileNotFoundError:
        status_label.config(text="FFmpeg introuvable.", fg="red")
        messagebox.showerror("Erreur", f"L'exécutable est absent ici :\n{chemin_ffmpeg}", parent=proc_window)
    
    
    close_btn = tk.Button(proc_window, text="Terminer et quitter", command=fermer_et_reset)
    close_btn.pack(pady=10)