# optical_flow_adder

## Softwares created
3 distincs softwares : <br>
### Video convertor : 
Converts a video into an .mkv file or .avi file. The .avi file is optimized for the optical flow computation. 

Here are multiple scenarios that are supported by the software : 

- If you have .mpe / .mpeg files, you can only give one file at a time. It will then ask you for a date/time of recording to add it to the .mkv file. The .mkv conversion is mandatory, the .avi for optical flow conversion is optional. 

- If you have one .mp4 / .mkv / ... file, the .mkv conversion and .avi for optical flow conversion are optional. However, you do need to select one of the two to validate. 

- If you have multiple .mp4 / .mkv / ... files, the script will sort them using the metadata in the files header. It will also make sure that the files don not have a gap between them. The file assembly is mandatory, the .mkv conversion and .avi for optical flow conversion are optional. 

### Video zone extractor : 
This software divides itself into 3 parts : 

- A video reader : it lets you select the frame you want to work with. Use the lateral bar to select the frame quickly, click on pause and then validate. 

- A zone extractor : use the magnifying glass logo to go to a specific region of the image, deselect the magnifying glass and then draw the rectangle using the mouse and the left clic. Once you are satisfied, tap on the "v" keyboard key to validate your selection. 

- The actual work : The software then extracts the selected zone on the whole video and adapts the format for optical flow extraction. 

### Optical flow adder : 
Takes the .avi file optimized for optical flow and computes optical flow. For each frame, the mean is computed which creates a 1D-signal. The result is added to the .edf file given. 

## Get started
### 1st case : You want to use the standalone softwares (.exe files)
Just download the three .exe files in the dist folder. Nothing else to install, you are good to go. 

### 2nd case : You want to reuse the code 
Follow these steps : 
- Install anaconda <a href="https://www.anaconda.com/download">on this website (anaconda.com)</a>
- In Anaconda prompt, type in these commands : 
``` powershell
> conda create -n edf_env python=3.10
> conda activate edf_env
```

- Download the 3 .exe files for ffmpeg using online ressource (only ffmpeg and ffprobe are mandatory) : <a href = "https://www.ffmpeg.org/download.html">ont this website (ffmpeg.org)</a> 


- Now do the following installations : 
```powershell
> conda install -c conda-forge av=9.2.0

> pip install pyinstaller pyedflib ffmpeg-python opencv-python tkcalendar pywin32 pywin32-ctypes

> pip install tkvideoplayer
```
- Now that you have created the environnement, move to the place with the 4 python codes using "cd" command
```powershell
cd <path to the python files>
```
- Now, you can launch the scripts using the front end scripts : 
```powershell
> python front_convert_video.py

> python main_video_zone_extractor.py

> python front_optical_flow_adder.py
```

If you want to recreate the the .exe files you can use the following commands : 
```powershell
> pyinstaller --onefile --noconsole --icon=images/video_logo.ico --add-data "images/video_logo.png;." --add-data "ffmpeg/ffmpeg.exe;." --add-data "ffmpeg/ffprobe.exe;." front_convert_video.py

> pyinstaller --onefile --noconsole --icon=images/logo_szfofe.ico --add-data "images/logo_szfofe.png;." --add-data "images/logo_szfofe.ico;." --add-data "ffmpeg/ffmpeg.exe;." main_video_zone_extractor.py

> pyinstaller --onefile --noconsole --icon=images/brain_logo.ico --add-data "images/brain_logo.png;." front_optical_flow_adder.py
```

## Images used
<a href="https://www.vecteezy.com/free-png/psychiatry">Psychiatry PNGs by Vecteezy</a> <br>
<a href="https://www.flaticon.com/fr/icones-gratuites/montage-video" title="montage vidéo icônes">Montage vidéo icônes créées par Freepik - Flaticon</a>
<a href="https://www.flaticon.com/fr/icones-gratuites/rogner" title="rogner icônes">Rogner icônes créées par Three musketeers - Flaticon</a>

## References
https://docs.opencv.org/3.4/d4/dee/tutorial_optical_flow.html

## Credits 
Jean-Eudes BORNERT <br>
ESIR 3 TIS - Université de Rennes

<img src="logo/ESIR%20I%20UnivRennes_quadri.png" alt="Logo ESIR | UR" width="300"/>
<img src="logo/logoLTSI.png" alt="Logo LTSI" width="150"/> 
<img src="logo/logo_chu.png" alt="Logo CHU" width="50"/>

