# Jean-Eudes BORNERT - LTSI - 30/03/2026
# Objectif    : Transformation de vidéos au format avi optimisé pour l'optical flow pour une zone spécifique
# Fonction    : Demande à l'utilisateur de définir une zone où extraire la vidéo (cadre)

# --------------------------------------
# Imports
# --------------------------------------
import matplotlib
matplotlib.use('TkAgg') 
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector
import matplotlib.image as mpimg

import processor_video_zone_extractor

coords = None

# --------------------------------------
# Fonctions
# --------------------------------------
def run_selector(img_path, icon_path=None):
    """ Ouvre l'image passée en paramètre et lance l'outil de sélection """
    global coords
    coords = None

    def onselect(eclick, erelease):
        global coords
        if eclick.xdata is None or erelease.xdata is None:
            return
            
        x1, y1 = int(eclick.xdata), int(eclick.ydata)
        x2, y2 = int(erelease.xdata), int(erelease.ydata)
        
        coords = (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))

    def on_key(event):
        if event.key in ['v', 'V']:
            if coords:
                print(f"Coordonnées validées : {coords}")
                plt.close() 
        elif event.key == 'escape':
            print("Opération annulée.")
            plt.close()

    try:
        img = mpimg.imread(img_path)
    except FileNotFoundError:
        print(f"Erreur : Image '{img_path}' non trouvée.")
        return None

    fig = plt.figure()
    fig.canvas.manager.set_window_title("1. Zoomez | 2. Dessinez | 3. Appuyez sur 'v'")
    
    try:
        icon_path = processor_video_zone_extractor.obtenir_chemin_ressource("logo_szfofe.ico", "images")
        fig.canvas.manager.window.iconbitmap(icon_path)
    except Exception as e:
        print(f"Avertissement : Impossible de charger l'icône Matplotlib ({e})")

    ax = fig.add_subplot(111)
    ax.imshow(img, aspect='equal')
    ax.axis('off')
    
    plt.subplots_adjust(left=0, bottom=0, right=1, top=1, wspace=0, hspace=0)
    
    global selector_obj 
    selector_obj = RectangleSelector(ax, onselect, useblit=True,
                                 button=[1], 
                                 minspanx=5, minspany=5,
                                 spancoords='pixels', interactive=True,
                                 props=dict(facecolor='none', edgecolor='lime', linewidth=2, alpha=0.8))

    fig.canvas.mpl_connect('key_press_event', on_key)
    print("Image ouverte. Dessinez le cadre, puis appuyez sur 'V'.")

    plt.show()
    return coords