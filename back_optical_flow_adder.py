# Jean-Eudes BORNERT - LTSI - 11/03/2026
# Objectif    : Extraction de l'optical flow de la vidéo de l'EEG et ajout d'un tracé représentant l'optical flow
# Fonction    : Code de base permettant d'écrire dans un fichier .edf
# Entrée      : fichier .edf, vidéo (format spécifique : .avi, noir et blanc, 320 px de large max) et nom de fichier de sortie
# Sortie      : fichier .edf avec le flux optique ajouté en dernière position

# --------------------------------------
# Imports
# --------------------------------------
import pyedflib
import numpy as np
import cv2
from datetime import timedelta
from concurrent.futures import ProcessPoolExecutor
import os
import multiprocessing

# --------------------------------------
# Calcul d'optical flow
# --------------------------------------
def compute_flow_segment(video_path, start_frame, end_frame, queue):
    cap = cv2.VideoCapture(video_path)
    start_lecture = max(0, start_frame - 1)
    cap.set(cv2.CAP_PROP_POS_FRAMES, start_lecture)
    
    segment_values = []
    ok, prev_frame = cap.read()
    if not ok:
        return f"Impossible de lire la vidéo {video_path}"
    
    prev_gray = prev_frame[:, :, 0] if len(prev_frame.shape) == 3 else prev_frame
    
    nb_frames = end_frame - start_frame
    for _ in range(nb_frames):
        ok, frame = cap.read()
        if not ok:
            return f"Impossible de lire la vidéo {video_path}"
            
        # Extraction du canal gris (zéro calcul mathématique)
        gray = frame[:, :, 0] if len(frame.shape) == 3 else frame
        
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None, 
            0.5, 3, 15, 3, 5, 1.2, 0
        )
        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])
        segment_values.append(np.mean(mag))
        
        prev_gray = gray
        queue.put(1)
        
    cap.release()
    return segment_values

# --------------------------------------
# Fonction Principale
# --------------------------------------
def process_edf(edf_path, video_path, output_name, log, set_progress):
    # -------------------------------------- 
    # Paramètres 
    # --------------------------------------
    log(f"EDF : {edf_path}")
    log(f"VIDEO : {video_path}")
    log(f"OUTPUT : {output_name}\n")
    log("")
    
    # --------------------------------------
    # Données sur la vidéo & vérifications
    # --------------------------------------
    log("Vérification de la vidéo...")

    # Format
    if not video_path.lower().endswith('.avi'):
        msg = "Erreur : La vidéo fournie doit impérativement être au format .avi"
        log("ECHEC\n" + msg)
        return msg
    
    # Intégrité
    cap = cv2.VideoCapture(video_path)
    ok, frame = cap.read()
    
    if not ok:
        msg = "Impossible de lire la vidéo."
        log("ECHEC\n" + msg)
        return msg
        
    # Largeur
    h, w = frame.shape[:2]
    if w > 320:
        msg = f"Erreur : La largeur de la vidéo ({w}px) dépasse la limite autorisée de 320px. Veuillez la redimensionner en amont."
        log("ECHEC\n" + msg)
        cap.release()
        return msg

    # Niveau de gris
    if len(frame.shape) == 3:
        b, g, r = cv2.split(frame)
        if not (np.allclose(b, g, atol=10) and np.allclose(g, r, atol=10)):
            msg = "Erreur : La vidéo n'est pas en Noir & Blanc. Veuillez la convertir en amont."
            log("ECHEC\n" + msg)
            cap.release()
            return msg

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_video = frame_count / fps
    cap.release()
    
    # --------------------------------------
    # Lecture EDF
    # --------------------------------------
    log("Lecture EDF...")
    reader = pyedflib.EdfReader(edf_path)
    duration_eeg = reader.file_duration
    n_samples = reader.getNSamples()[0]
    n_channels = reader.signals_in_file
    freq_edf = reader.getSampleFrequency(0)
    signal_headers = reader.getSignalHeaders()
    header = reader.getHeader()
    signals = [reader.readSignal(i) for i in range(n_channels)]
    reader.close()
    
    # --------------------------------------
    # Synchronisation des données
    # --------------------------------------
    
    # TODO : Voir si on ne fait pas plutôt en sorte de synchroniser les heures de debut des deux éléments. 
    tolerance_duree = 1.0
    ecart_duree = abs(duration_eeg-duration_video)
    if ecart_duree > tolerance_duree:
        msg = f"La vidéo et le tracé EEG ont un écart de durée trop important (> {tolerance_duree}s).\nDurée EEG : {timedelta(seconds=duration_eeg)}\nDurée vidéo : {timedelta(seconds=duration_video)}\nÉcart constaté : {ecart_duree:.2f}s"
        log("ECHEC\n" + msg)
        return msg
    else:
        log(f"Durée EEG   : {timedelta(seconds=duration_eeg)}")
        log(f"Durée vidéo : {timedelta(seconds=duration_video)}\n")
        if ecart_duree > 0:
            log(f"(Écart toléré de {ecart_duree:.3f}s)\n")
    
    # --------------------------------------
    # Remplissage du canal d'optical flow
    # --------------------------------------
    log("Calcul d'optical flow...")
    manager = multiprocessing.Manager()
    queue = manager.Queue()

    # Heuristique intelligente : 1 coeur par tranche de 50 images
    max_cores = os.cpu_count() or 4
    num_workers = max(1, min(max_cores, frame_count // 50))
    frames_per_worker = frame_count // num_workers
    futures = []

    log(f"Calcul en parallèle sur {num_workers} coeurs...")

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        for i in range(num_workers):
            start = i * frames_per_worker
            end = frame_count if i == num_workers - 1 else (i + 1) * frames_per_worker
            if i != 0: start -= 1
            futures.append(executor.submit(compute_flow_segment, video_path, start, end, queue))

        total_processed = 0
        while any(not f.done() for f in futures) or not queue.empty():
            while not queue.empty():
                queue.get()
                total_processed += 1
                set_progress((total_processed / frame_count) * 90)

        all_video_mvt = []
        for i, f in enumerate(futures):
            res = f.result()
            if isinstance(res, str): return res
            if i != 0: res = res[1:]
            all_video_mvt.extend(res)

    # --------------------------------------
    # On met les deux éléments à la même 
    # fréquence, celle du fichier EDF
    # --------------------------------------
    log("Ajustement de la vidéo avec l'EEG...")
    new_signal = np.zeros(n_samples)
    max_idx = len(all_video_mvt) - 1
    current_frame_idx = 0
    
    for i in range(n_samples):
        frame_cible = int((i / freq_edf) * fps)
        if current_frame_idx < frame_cible: 
            current_frame_idx = min(frame_cible, max_idx)
        new_signal[i] = all_video_mvt[current_frame_idx] 

    # --------------------------------------
    # Normalisation par rapport au max (% de mvt)
    # --------------------------------------
    max_sig = np.max(new_signal)
    if max_sig > 0:
        new_signal = (new_signal * 100) / max_sig

    # --------------------------------------
    # Ajout du nouveau canal au fichier .edf
    # --------------------------------------
    new_header = signal_headers[0].copy()
    new_header["label"] = "Optical flow"
    signals.append(new_signal)
    signal_headers.append(new_header)

    # --------------------------------------
    # Ecriture du nouveau fichier
    # --------------------------------------
    log("Ecriture du fichier...")
    writer = pyedflib.EdfWriter(output_name, len(signals), file_type=pyedflib.FILETYPE_EDFPLUS)
    writer.setHeader(header)
    writer.setSignalHeaders(signal_headers)
    writer.writeSamples(signals)
    writer.close()

    set_progress(100)

    # --------------------------------------
    # Message de succès
    # --------------------------------------
    log(f"Le fichier a bien été enregistré : {output_name}")