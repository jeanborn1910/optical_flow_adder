# Jean-Eudes BORNERT - LTSI - 30/03/2026
# Objectif    : Transformation de vidéos au format avi optimisé pour l'optical flow pour une zone spécifique
# Fonction    : Interface principale, lecteur vidéo, sélection d'une image pour définir le cadre

# --------------------------------------
# Imports
# --------------------------------------
import datetime
import tkinter as tk
from tkinter import filedialog
from tkVideoPlayer import TkinterVideo
import cv2
import os

import selector_video_zone_extractor
import processor_video_zone_extractor

interface_affichee = False
current_video_path = ""

# --------------------------------------
# Fonctions
# --------------------------------------
def reset_interface():
    global interface_affichee, current_video_path, vid_player
    
    try:
        vid_player.destroy()
    except:
        pass
        
    vid_player = TkinterVideo(scaled=True, master=root)
    vid_player.bind("<<Duration>>", update_duration)
    vid_player.bind("<<SecondChanged>>", update_scale)
    vid_player.bind("<<Ended>>", video_ended)
    
    play_pause_btn.pack_forget()
    progress_frame.pack_forget()
    valider_btn.pack_forget()
    
    interface_affichee = False
    current_video_path = ""
    
    root.deiconify()
    root.attributes('-topmost', True)
    root.update()
    root.attributes('-topmost', False)
    root.focus_force()

def update_duration(*args):
    duration = int(vid_player.video_info()["duration"])
    end_time["text"] = str(datetime.timedelta(seconds=duration))
    progress_slider["to"] = duration

def update_scale(*args):
    current_time = int(vid_player.current_duration())
    progress_value.set(current_time)
    start_time["text"] = str(datetime.timedelta(seconds=current_time))

def load_video():
    global interface_affichee, current_video_path
    file_path = filedialog.askopenfilename()

    if file_path:
        current_video_path = file_path
        vid_player.load(file_path)

        progress_slider.config(to=0, from_=0)
        play_pause_btn["text"] = "Pause"
        progress_value.set(0)

        if not interface_affichee:
            vid_player.pack(expand=True, fill="both")
            play_pause_btn.pack()
            progress_frame.pack(fill="x", padx=10, pady=5)
            valider_btn.pack(pady=10)
            
            interface_affichee = True
        
        vid_player.play()

def seek(value):
    vid_player.seek(int(value))

def play_pause():
    if vid_player.is_paused():
        vid_player.play()
        play_pause_btn["text"] = "Pause"
    else:
        vid_player.pause()
        play_pause_btn["text"] = "Lecture"

def video_ended(event):
    progress_slider.set(progress_slider["to"])
    play_pause_btn["text"] = "Lecture"
    progress_slider.set(0)
    start_time["text"] = str(datetime.timedelta(seconds=0))

def valider_action():
    """ Extrait la frame actuelle, cache l'interface et ouvre l'outil de sélection """
    if not current_video_path:
        return

    root.withdraw()

    if not vid_player.is_paused():
        play_pause()

    current_time = vid_player.current_duration()

    cap = cv2.VideoCapture(current_video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, current_time * 1000)
    ok, frame = cap.read()
    cap.release()

    if ok:
        temp_image_path = "temp_frame.png"
        cv2.imwrite(temp_image_path, frame)
        
        coords = selector_video_zone_extractor.run_selector(temp_image_path, chemin_image)
        
        if coords:
            print("Lancement du traitement...")
            processor_video_zone_extractor.process_video(current_video_path, coords, on_complete=reset_interface)
        else:
            root.deiconify()
            
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
    else:
        root.deiconify()
        print("Erreur d'extraction.")

# --------------------------------------
# Fenêtre principale
# --------------------------------------
root = tk.Tk()

root.title("specific zone converter for optical flow")
chemin_image = processor_video_zone_extractor.obtenir_chemin_ressource("logo_szfofe.png", "images")
try:
    img_tk = tk.PhotoImage(file=chemin_image)
    root.iconphoto(True, img_tk)
except Exception:
    pass

root.geometry("600x400") 

load_btn = tk.Button(root, text="Charger la vidéo", command=load_video)
load_btn.pack(pady=10)

vid_player = TkinterVideo(scaled=True, master=root)
play_pause_btn = tk.Button(root, text="Lecture", command=play_pause)

progress_frame = tk.Frame(root)

start_time = tk.Label(progress_frame, text=str(datetime.timedelta(seconds=0)))
progress_value = tk.IntVar(root)
progress_slider = tk.Scale(progress_frame, variable=progress_value, from_=0, to=0, orient="horizontal", command=seek, showvalue=False)
end_time = tk.Label(progress_frame, text=str(datetime.timedelta(seconds=0)))

start_time.pack(side="left", anchor="s", pady=(0,2))
progress_slider.pack(side="left", fill="x", expand=True, padx=5, anchor="center")
end_time.pack(side="left", anchor="s", pady=(0,2))

valider_btn = tk.Button(root, text="Valider", bg="green", fg="white", command=valider_action)

vid_player.bind("<<Duration>>", update_duration)
vid_player.bind("<<SecondChanged>>", update_scale)
vid_player.bind("<<Ended>>", video_ended)

root.mainloop()