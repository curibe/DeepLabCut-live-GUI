from tkinter import BooleanVar, StringVar
from typing import Optional

import typer
from wasabi import Printer

from stream_mode import ServerDLCLiveGUI
from zmq_mode import ZMQDLCLiveGUI
from tools import SubscriberClient

app = typer.Typer()

camera_app = typer.Typer(
    help="Allow to apply update operations over camera config"
)
app.add_typer(camera_app, name="camera")

zmq_reader_app = typer.Typer()
app.add_typer(zmq_reader_app, name="zmqreader")

# dlclive_app = typer.Typer(
#     help="Allow to apply update operations over DLC pipeline config"
# )
# app.add_typer(dlclive_app, name="dlc")

msg = Printer()


@camera_app.command("change-config")
def camera_change_config(
    device: Optional[str] = typer.Option(None, "--device", "-dv"),
    resolution: Optional[str] = typer.Option(None, "--size", "-s"),
    fps: Optional[int] = typer.Option(None, "--fps", "-r"),
    filename:  Optional[str] = typer.Option(None, "--file", "-f")
):
    """Change camera parameters in json config file

    You can change the device id/url, the resolution, fps(frame per seconds).
    Also you can specify the name of the json file (without .json)

    If --file is not specify, DLC will use the default file founded in
    the config directory located in /home/<user>/DeepLabCut-live-GUI/config.

    If no options are not provided, a warning message will be raised.

    For --size you can write for example: 640,480 or 640x480 or 640:480


    Example:

    $ python run_simulation camera change-config --device rtsp://localhost:8555 
    --size 100x100 --fps 60 --file config_file
    """
    args = locals()
    args.pop("filename")
    if not all(x is None for x in args.values()):
        dlcgui = ServerDLCLiveGUI(ffmpeg=False)

        if filename:
            dlcgui.get_config(filename)

        msg.info(f"Updating file ...{dlcgui.cfg_file}")
        dlcgui.get_config(dlcgui.cfg_name.get())
        dlcgui.edit_cam_settings(args)
        msg.good("Configuration file succesfull updated")
    else:
        msg.warn("Nothing to change. You did not pass arguments")


@app.command()
def stream_ffmpeg(
    server: Optional[str] = typer.Option("rtsp", "--server")
):
    """Run DeepLabCut pipeline reading video from rtmp or rtsp stream server

    You can specify the server with the option --server. The server could be 
    rtsp or rtmp.
    
    If no server is provided, It will read video from a rtsp server by default
    
    his pipeline will deliver the results using the same server, using ffmpeg

    """

    dlc = ServerDLCLiveGUI(mode=server)
    # set options setted in gui
    dlc.dlc_option = StringVar(value="dlclive-test")
    dlc.display_keypoints = BooleanVar(value=True)
    dlc.change_display_keypoints()

    msg.divider("Init cam")
    dlc.init_cam()

    msg.divider("Running dlc analysis")
    dlc.init_dlc()

    dlc.run()


@app.command()
def stream_zmq(
    send: Optional[str] = typer.Option("video", '--send', '-s')
):
    """Run DeepLabCut pipeline reading video from rtsp stream server

    This pipeline will deliver the results using zeromq

    """
    dlc = ZMQDLCLiveGUI(send=send)

    # set options setted in gui
    dlc.dlc_option = StringVar(value="dlclive-test")
    dlc.display_keypoints = BooleanVar(value=True)
    dlc.change_display_keypoints()

    msg.divider("Init cam")
    dlc.init_cam()

    msg.divider("Running dlc analysis")
    dlc.init_dlc()

    dlc.run()

@zmq_reader_app.command('read')
def read_zmq(
    ip: Optional[str] = typer.Option("localhost", '--ip'),
    url: Optional[str] = typer.Option("", '--url'),
    recv: Optional[str] = typer.Option("video", '--recv')
):
    
    client = SubscriberClient(ip=ip, url=url)
        
    client.start()

    if recv == "poses":
        for pose in client.get_poses():
            print("pose: ", pose)
    elif recv == "video":
        print("get frame")
        client.get_frames()

    else:
        msg.warn("no options")

    client.end()
    

if __name__ == "__main__":
    app()
