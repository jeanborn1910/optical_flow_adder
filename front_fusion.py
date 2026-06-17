import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
import threading
import os
import time

from back_fusion import analyser_videos_vwr, obtenir_chemin_ressource

class ApplicationVWR(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Assembleur de Vidéos VWR")
        self.geometry("700x500")
        self.configure(padx=20, pady=20)

        chemin_image = obtenir_chemin_ressource("merge.png", "images")
        try:
            self.img_tk = tk.PhotoImage(file=chemin_image)
            self.iconphoto(True, self.img_tk)
        except Exception as e:
            print(f"Avertissement : Icône introuvable ({e})")

        # Variables Tkinter
        self.chemin_fichier = tk.StringVar()
        
        self.creer_widgets()

    def creer_widgets(self):
        frame_haut = tk.Frame(self)
        frame_haut.pack(fill=tk.X, pady=(0, 20))

        tk.Label(frame_haut, text="Fichier .vwr à traiter :", font=("Arial", 10, "bold")).pack(anchor="w")
        
        frame_input = tk.Frame(frame_haut)
        frame_input.pack(fill=tk.X, pady=5)
        
        tk.Entry(frame_input, textvariable=self.chemin_fichier, width=70).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        tk.Button(frame_input, text="Parcourir...", command=self.choisir_fichier).pack(side=tk.RIGHT)

        # --- Message d'avertissement ---
        texte_attention = (
            "Attention : Assurez-vous que l'ensemble des vidéos associées au fichier .vwr\n"
            "soient localisées au même endroit que le fichier .vwr.\n"
            "Également, assurez-vous que les données ne soient pas sur un\n"
            "disque dur externe pour des soucis de rapidité."
        )
        tk.Label(
            self, 
            text=texte_attention, 
            font=("Arial", 11, "bold"), 
            fg="#d9534f",
            justify="left"
        ).pack(pady=(5, 5))

        # --- Bouton de lancement ---
        self.btn_lancer = tk.Button(self, text="Lancer l'assemblage", font=("Arial", 12, "bold"), bg="green", fg="white", command=self.demarrer_traitement)
        self.btn_lancer.pack(pady=(5, 15))

        # --- Console de logs ---
        tk.Label(self, text="Console d'exécution :", font=("Arial", 10, "bold")).pack(anchor="w")
        
        self.console = scrolledtext.ScrolledText(self, wrap=tk.WORD, height=15, font=("Consolas", 9), bg="white", fg="black")
        self.console.pack(fill=tk.BOTH, expand=True)

    def choisir_fichier(self):
        fichier = filedialog.askopenfilename(
            title="Sélectionner un fichier VWR",
            filetypes=[("Fichiers VWR", "*.vwr"), ("Tous les fichiers", "*.*")]
        )
        if fichier:
            self.chemin_fichier.set(fichier)

    def ecrire_log(self, message):
        self.after(0, self._inserer_texte, message)

    def _inserer_texte(self, message):
        self.console.config(state=tk.NORMAL)
        self.console.insert(tk.END, str(message) + "\n")
        self.console.see(tk.END) 
        self.console.config(state=tk.DISABLED)

    def demarrer_traitement(self):
        chemin = self.chemin_fichier.get()
        if not chemin:
            messagebox.showwarning("Attention", "Veuillez d'abord sélectionner un fichier .vwr")
            return

        # Désactiver le bouton pendant le traitement
        self.btn_lancer.config(
            state=tk.DISABLED, 
            text="Traitement en cours...",
            bg="#888888",
            disabledforeground="white"
        )
        self.console.config(state=tk.NORMAL)
        self.console.delete(1.0, tk.END)
        self.console.config(state=tk.DISABLED)

        # Lancer le script dans un thread séparé
        thread = threading.Thread(target=self.executer_backend, args=(chemin,))
        thread.daemon = True 
        thread.start()

    def executer_backend(self, chemin):
        debut_chrono = time.time()
        succes = False
        
        try:
            succes = analyser_videos_vwr(chemin, log_callback=self.ecrire_log)
        except Exception as e:
            self.ecrire_log(f"\nErreur inattendue : {e}")
            succes = False
            
        duree = time.time() - debut_chrono
        self.ecrire_log(f"\nTemps total d'exécution : {duree:.2f} secondes")
        
        self.after(0, self._reactiver_bouton, succes)

    def _reactiver_bouton(self, succes):
        self.btn_lancer.config(
            state=tk.NORMAL, 
            text="Lancer l'assemblage",
            bg="#4CAF50",
            fg="white"
        )
        if succes:
            messagebox.showinfo("Terminé", "L'assemblage de la vidéo est terminé avec succès !")
        else:
            messagebox.showerror("Erreur", "Une erreur est survenue pendant le traitement.\nVeuillez vérifier la console pour plus de détails.")

if __name__ == "__main__":
    app = ApplicationVWR()
    app.mainloop()