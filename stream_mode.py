import re
import subprocess
from tkinter import BooleanVar, StringVar

import numpy as np
from PIL import Image, ImageDraw
from wasabi import Printer

from dlclivegui import DLCLiveGUI

msg = Printer()


def get_value_by_key(k, d):
    """Get the value of a key in a nested dict

    Args:
        k (str): key
        d (dict): nested dictionary

    Returns:
        value: value associated to the key. Return None if
               the key does not exist.

    """
    if k in d:
        return d[k]

    for v in d.values():
        if isinstance(v, dict):
            a = get_value_by_key(k, v)
            if a is not None:
                return a
    return None


class ServerDLCLiveGUI(DLCLiveGUI):
    """Open a server to send and receie video streaming by rtmp or rtsp

    Args:
        DLCLiveGUI (class): GUI of DeepLabCut Live project to send video in
                            realtime using camera.
    """

    def __init__(self, ffmpeg=True, mode="rtsp"):
        """Initialize the server to analyse the recevied video using DLCLive

        Args:
            ffmpeg (bool, optional): To able the server return a video with
                                     the poses using ffmpeg. Defaults to True.
            mode (str, optional): To choose the type of stream server(rstp,rtmp).
                                  Defaults to "rtsp".
        """

        super().__init__()

        if ffmpeg:
            if mode == "rtsp":
                option = "rtsp"
                self.server_output_url = "rtsp://localhost:8554/output"
            if mode == "rtmp":
                option = "flv"
                self.server_output_url = "rtmp://localhost:1935/output"

            resolution = self.cfg.get('resolution')
            width = resolution[0] if resolution else 200
            height = resolution[1] if resolution else 200
            fps = get_value_by_key("fps", self.cfg)
            fps = fps if fps is not None else 30

            # command and params for ffmpeg
            command = ['ffmpeg',
                       '-y',
                       '-f', 'rawvideo',
                       '-vcodec', 'rawvideo',
                       '-pix_fmt', 'rgb24',
                       '-s', "{}x{}".format(width, height),
                       '-r', '{}'.format(fps),
                       '-i', '-',
                       '-c:v', 'libx264',
                       '-pix_fmt', 'yuv420p',
                       '-preset', 'ultrafast',
                       '-f', option,
                       self.server_output_url]

            self.p = subprocess.Popen(command, stdin=subprocess.PIPE)

    def display_frame(self):
        """ Display a frame in display window
        """

        if self.cam_pose_proc and self.display_window:

            frame = self.cam_pose_proc.get_display_frame()

            if frame is not None:

                img = Image.fromarray(frame)
                if frame.ndim == 3:
                    b, g, r = img.split()
                    img = Image.merge("RGB", (r, g, b))

                pose = (
                    self.cam_pose_proc.get_display_pose()
                    if self.display_keypoints.get()
                    else None
                )

                if pose is not None:

                    im_size = (frame.shape[1], frame.shape[0])

                    if not self.display_colors:
                        self.set_display_colors(pose.shape[0])

                    img_draw = ImageDraw.Draw(img)

                    for i in range(pose.shape[0]):
                        if pose[i, 2] > self.display_lik_thresh:
                            try:
                                x0 = (
                                    pose[i, 0] - self.display_radius
                                    if pose[i, 0] - self.display_radius > 0
                                    else 0
                                )
                                x1 = (
                                    pose[i, 0] + self.display_radius
                                    if pose[i, 0] + self.display_radius < im_size[1]
                                    else im_size[1]
                                )
                                y0 = (
                                    pose[i, 1] - self.display_radius
                                    if pose[i, 1] - self.display_radius > 0
                                    else 0
                                )
                                y1 = (
                                    pose[i, 1] + self.display_radius
                                    if pose[i, 1] + self.display_radius < im_size[0]
                                    else im_size[0]
                                )
                                coords = [x0, y0, x1, y1]
                                img_draw.ellipse(
                                    coords,
                                    fill=self.display_colors[i],
                                    outline=self.display_colors[i],
                                )
                            except Exception as e:
                                print(e)

                    lastimg = np.asarray(img)
                    self.send_numpy_frame_to_ffmpeg(lastimg)

            self.display_frame_label.after(10, self.display_frame)

    def update_camera_settings(self, names, entries, dtypes):
        """ Update camera settings from values input in settings GUI
        """

        for name, entry, dt in zip(names, entries, dtypes):
            val = entry
            val = val.split(",")
            val = [v.strip() for v in val]
            try:
                if dt is bool:
                    val = [True if v == "True" else False for v in val]
                elif name == "device" and isinstance(entry, str):
                    val = [v if v else None for v in val]
                else:
                    val = [dt(v) if v else None for v in val]
            except TypeError:
                pass

            val = val if len(val) > 1 else val[0]
            self.set_camera_param(name, val)

        self.save_config()

    def edit_cam_settings(self, args):
        """ GUI window to edit camera settings
        """

        arg_names, arg_vals, arg_dtypes, arg_restrict = self.get_cam_args()

        for arg_name, arg_value in args.items():
            if arg_value:
                msg.info(f"Changing {arg_name}... ")
                idx = arg_names.index(arg_name)
                if arg_name == "resolution":
                    arg_vals[idx] = [
                        int(x) for x in re.split("[,:x]", arg_value)
                    ]
                else:
                    arg_vals[idx] = arg_value
                msg.good(f"{arg_name} updated to {arg_value}")

        entry_vars = []
        for n, v in zip(arg_names, arg_vals):

            if type(v) is list:
                v = [str(x) if x is not None else "" for x in v]
                v = ", ".join(v)
            else:
                v = v if v is not None else ""
            entry_vars.append(str(v))

            if n in arg_restrict.keys():
                restrict_vals = arg_restrict[n]
                if type(restrict_vals[0]) is list:
                    restrict_vals = [
                        ", ".join([str(i) for i in rv]) for rv in restrict_vals
                    ]

        self.update_camera_settings(arg_names,
                                    entry_vars,
                                    arg_dtypes)

    def send_numpy_frame_to_ffmpeg(self, frame):
        """send frame as numpy array using ffmpeg

        Args:
            frame (np.ndarray): frame with poses as a numpy array
        """

        if frame is not None:
            # write to pipe
            self.p.stdin.write(frame.tobytes())


def main():
    """Run all the pipeline
    """

    dlc = ServerDLCLiveGUI()

    # set options setted in gui
    dlc.dlc_option = StringVar(value="dlclive-test")
    dlc.display_keypoints = BooleanVar(value=True)
    dlc.change_display_keypoints()

    msg.divider("Init cam")
    dlc.init_cam()

    msg.divider("Running dlc analysis")
    dlc.init_dlc()

    dlc.run()


if __name__ == "__main__":
    main()
