# NeuroCAAS RTSP-ZMQ instructions

This document contains the steps to send a video to an RTSP server and get it back after the ML pipeline using zeromq. The test uses the DLCLiveGUI library to run an ML process to infer poses. This requires the use of a model with trained data so that we use the example used in the benchmark of DLCLive. The video used is [dog_clip.avi](https://github.com/DeepLabCut/DeepLabCut-live/blob/master/check_install/dog_clip.avi)

## Requirements

**System dependencies**
 - ffmpeg
 > **Install ffmpeg in linux:**
 > ```bash
 > sudo apt update
 > sudo apt install ffmpeg
 > ffmpeg -version
 > ```
 > **Install ffmpeg in OSX:**
 > ```bash
 > brew install ffmpeg
 > ```


**Python dependencies**

```
opencv
typer
wasabi
pyzmq
numpy
pillow
pandas
multiprocess
colorcet
tqdm
serial
imutils
pytz
```

There are several libraries because we overwrite some dlclive-gui functions, so that it requires some of its dependencies

You also need to clone the [DeepLabCut-live-GUI fork](https://github.com/curibe/DeepLabCut-live-GUI/tree/master) repository and switch to the branch `rtmp-livestream` 


:::info
you can create a virtual enviroment with python if you wish:
```
python3 -m venv <name>
source <name>/bin/activate
```
or use another python virtual environment manager
To install, you can run pip:
```bash
pip install -r requirements-live.txt
```
:::

To validate it is working, please run this command:

```bash
python run_simulation.py zmqreader read 
```
    
## Send video to rtsp server

To send the video you will make use of FFmpeg. You can run the command directly or use the following script to do it:

```bash!
bash send_video.sh [ip] [mode] [fps]


  OPTION:
  -------

  - ip [defaul localhost]: public ip of the ec2 server 

  - mode:
      - notime [default]        
      - time   : to send video with timestamp written over it
      - nframe : to send video with frame number written over it
      - timeframe   : to send video with timestamp and frame number written over it

  - size [default 200x200]: to stablish the frame size

  - fps [default 30]: to stablish the frame per seconds of the video


 EXAMPLE:
 --------
 bash send_video.sh 1.2.3.4 time 200x200 30 

```

To send the video with timestamp written over it, using the script, you must run this:
```bash 
bash send_video.sh <ip> time
```
    
To send the video without timestamp written over it, using the script, you must run this:
```bash
bash send_video <ip>
```

In all cases, the video is sent in streaming mode, in an infinite loop (`-re -stream_loop -1`) and with a size of 200x200 by default. The smaller the image, the faster the ML pipeline will run.
    

### Reproduce the _mirror_ video

To validate if the RTSP server is receiving the video, you can reproduce the mirror video (without ML process) just reading it from the server:

```bash
ffplay rtsp://<ip>:8554/input
```

or by using the python script `read_video_mirror.py` to play it with opencv:
```
python read_video_mirror.py <ip>
```

    
## Run the ML process in the server side

To run different tests, we launch the same EC2 with id `i-07c695248625b3b04`  
![](https://docs.monadical.com/uploads/upload_0b6be4d06cacf50b80cad235a32e28ed.png)

This is because we connect to it by ssh and run manually the ML process and try different configurations.
We need to move to the dir DeepLabCut-live-GUI to run the process

### Run process to send frames with poses

Run the ML process to analyze the video and send frames with poses (by default) to the client zmq

```bash
# Server side
xvfb-run python run_simulation.py stream-zmq --send video #default
```
This mode is by default so that it is not required to write the option `--send video`

### Run process to send poses

Run the ML process to analyze the video and send poses (ndarray) to the client zmq
```bash
# Server side
xvfb-run python run_simulation.py stream-zmq --send poses
```

## ==Read the returned data==

You can read the result in two ways:
 - Receive the frames with poses included and reproduce them with OpenCV
 - Receive the poses array

### Receive the frames with poses

To see the help of the client, you can run this:

```bash
#1. [Optional] Show help
python run_simulation.py zmqreader read --help

OUTPUT:

Usage: run_simulation.py zmqreader read [OPTIONS]

  Run ZMQ subscriber to read video/poses sent by the server

Options:
  --ip TEXT       [default: localhost]
  --url TEXT      [default: ]
  --recv TEXT     [default: video]
  --thrmode TEXT  [default: None]  (values: get, show, both)
  --help          Show this message and exit.

```

where the option `thrmode` is used to run the client process with multithreading. You can puth in a thread the process of *get* the frame, *show* the frame or *both*. If this option is None, it will run all in the same thread.


To begin to receive the video, you must run this in the terminal:
```bash
#2. Run reader
python run_simulation.py zmqreader read --recv video --ip <ip>
```

It will open an OpenCV's window where the video is shown.  

You can run this process which shows the processed video, and  the FFplay (or read_video_mirror.py) command in another terminal to reproduce the mirror video to compare both and check the latency

### Receive the poses

Run the client in command line:

```bash
#Run reader
python run_simulation.py zmqreader read --recv poses --ip <ip>
```
It will only print the poses in the command line, but you can do something else with them like save them in a file or send them to other places


## Take the screenshot

If you want to take a screenshot of both videos (mirror and processed) to compare and measure the latency, you can use this script in python:

```python
    
from PIL import ImageGrab
from datetime import datetime
import pytz
import re

#image = ImageGrab.grab(bbox=(1*384,340,4*384,840))
image = ImageGrab.grab(bbox=(0,0,1920,1080))
# you can define your own time zone
mytime = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
mytime = re.sub("[-:\s\.]","_",mytime)
image.save(f'screenshot_{mytime}.png')
```

You can set or not the time zone. As the latencies are in the order of seconds, the time difference does not matter in this case.