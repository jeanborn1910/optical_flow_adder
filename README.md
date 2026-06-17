# optical_flow_adder

## Softwares created
4 distincs softwares : <br>
### 1. Video convertor : 
Converts a video into a ```standard .mp4``` file or ```.mp4 for optical flow``` file. The .mp4 for optical flow file is optimized for the optical flow computation (black and white, no sound, 340 px wide). 

Here are multiple scenarios that are supported by the software : 

- If you have ```.mpe``` / ```.mpg``` / ```.mpeg``` files, you can only give one file at a time. It will then ask you for a date/time of recording to add it to the standard .mp4 file. The ```standard .mp4``` conversion is mandatory, the ```.mp4 for optical flow``` conversion is optional. 

- If you have one ```.mp4``` / ```.mkv``` / ... file, the ```standard .mp4``` conversion and ```.mp4 for optical flow``` conversion are optional. However, you do need to select one of the two to validate. 

- If you have multiple ```.mp4``` / ```.mkv``` / ... files, the script will sort them using the metadata in the files header. It will also make sure that the files do not have a gap between them. The file assembly is mandatory, the ```standard .mp4``` conversion and ```.mp4 for optical flow``` conversion are optional. 

### 2. Video fusion
The idea behind this software is to use a proprietary format ```.vwr``` file to extract the timeline in case multiple videos are associated to one EEG. With this software, anyone can synchronize all video files to its corresponding EEG. 

### 3. Video zone extractor : 
This software divides itself into 3 parts : 

- A video reader : it lets you select the frame you want to work with. Use the lateral bar to select the frame quickly, click on pause and then validate. 

- A zone extractor : use the magnifying glass logo to go to a specific region of the image, deselect the magnifying glass and then draw the rectangle using the mouse and the left clic. Once you are satisfied, tap on the ```v``` keyboard key to validate your selection. 

- The actual work : The software then extracts the selected zone on the whole video and adapts the format for optical flow extraction. 

### 4. Optical flow adder : 
Takes the ```.mp4 for optical flow``` file optimized for optical flow and computes optical flow. For each frame, the mean is computed which creates a 1D-signal. The result is added to the .edf file given. 

## Get started
### 1st case : You want to use the standalone softwares (.exe files)
Just download the three ```.exe``` files in the release section and you are good to go !

### 2nd case : You want to reuse the code 
Follow these steps : 
- Install anaconda <a href="https://www.anaconda.com/download">on this website (anaconda.com)</a>
- In Anaconda prompt, type in these commands : 
``` powershell
> conda create -n edf_env python=3.10
> conda activate edf_env
```

- Download the 4 ```.exe``` files for ffmpeg using online ressource (only ffmpeg and ffprobe are mandatory) : <a href = "https://www.ffmpeg.org/download.html">ont this website (ffmpeg.org)</a> 

- Now do the following installations : 

```powershell
> conda install -c conda-forge av=9.2.0

> pip install pyinstaller pyedflib ffmpeg-python opencv-python tkcalendar matplotlib pywin32 pywin32-ctypes

> pip install tkvideoplayer
```

Nb : the first line is to make ```tkvideoplayer``` install work. 

- Now that you have created the environnement, move to the place with the 4 python codes using ```cd``` command

```powershell
cd <path to the python files>
```
- Now, you can launch the scripts using the front end scripts : 

```powershell
> python front_convert_video.py

> python main_video_zone_extractor.py

> python front_optical_flow_adder.py
```

If you want to recreate the the ```.exe``` files you can use the following commands : 
```powershell
> pyinstaller --onefile --noconsole --icon=images/video_logo.ico --add-data "images/video_logo.png;." --add-data "ffmpeg/ffmpeg.exe;." --add-data "ffmpeg/ffprobe.exe;." front_convert_video.py

> pyinstaller --onefile --noconsole --icon=images/logo_szfofe.ico --add-data "images/logo_szfofe.png;." --add-data "images/logo_szfofe.ico;." --add-data "ffmpeg/ffmpeg.exe;." front_video_zone_extractor.py

> pyinstaller --onefile --noconsole --icon=images/brain_logo.ico --add-data "images/brain_logo.png;." front_optical_flow_adder.py

> pyinstaller --onefile --noconsole --icon=images/merge.ico --add-data "images/merge.png;." --add-data "ffmpeg;ffmpeg" front_fusion.py
```

## Images used
<a href="https://www.vecteezy.com/free-png/psychiatry">Psychiatry PNGs by Vecteezy</a> <br>
<a href="https://www.flaticon.com/fr/icones-gratuites/montage-video" title="montage vidéo icônes">Montage vidéo icônes créées par Freepik - Flaticon</a> <br>
<a href="https://www.flaticon.com/fr/icones-gratuites/rogner" title="rogner icônes">Rogner icônes créées par Three musketeers - Flaticon</a><br>
<a href="https://www.flaticon.com/free-icons/video-editing" title="video editing icons">Video editing icons created by Hilmy Abiyyu A. - Flaticon</a>

## References
https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html

## Credits 
Jean-Eudes BORNERT <br>
ESIR 3 TIS - Université de Rennes

<img src="logo/ESIR%20I%20UnivRennes_quadri.png" alt="Logo ESIR | UR" width="300"/>
<img src="logo/logoLTSI.png" alt="Logo LTSI" width="150"/> 
<img src="logo/logo_chu.png" alt="Logo CHU" width="50"/>

