import time
from tkinter import BooleanVar, StringVar

import numpy as np
import zmq
from PIL import Image, ImageDraw
from wasabi import Printer

from dlclivegui import DLCLiveGUI

msg = Printer()


class ZMQDLCLiveGUI(DLCLiveGUI):
    """Open a zmq socket and send images/poses arrays

    Open a ZMQ socket as PUB-SUB and send the images with poses or
    poses only to the client/subscriber

    Args:
        DLCLiveGUI (class): DeepLabCutLive-GUI to configure the
                            Machine Learning pipeline and receive
                            images.
    """

    def __init__(self, send='video'):
        """Initialize the DLCLive-GUI and zmq socket

        Args:
            send (str, optional): To set if video or poses will
                                  be sent back. Defaults to 'video'.
        """
        url = "tcp://*:1936"
        self.ctxzmq = zmq.Context()
        self.sock = self.ctxzmq.socket(zmq.PUB)
        self.sock.bind(url)
        self.send = send

        super().__init__()

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
                    if self.send == "video":
                        self.send_image_by_zmq(img)
                    elif self.send == "poses":
                        self.send_numpy_array_by_zmq(pose)
                    else:
                        pass

            self.display_frame_label.after(10, self.display_frame)

    def send_numpy_array_by_zmq(self, pose):
        """Send numpy array using zmq

        Args:
            pose (ndarray): poses as a numpy array
        """

        if pose is not None:
            self.send_array(pose, copy=False)

    def send_image_by_zmq(self, image):
        """Send image or frame as a numpy array using zqm

        Args:
            image (Pillow Image): Image with poses
        """
        image_array = np.asarray(image)
        if image_array.flags['C_CONTIGUOUS']:
            self.send_array(image_array, copy=False)
        else:
            image_array = np.ascontiguousarray(image_array)
            self.send_array(image_array, copy=False)

    def send_array(self, A, flags=0, track=False, copy=True):
        """Send numpy array with metadata

        Send numpy array with metadata required to reconstruct
        the array (dtype,shape)

        Args:
            A (ndarray): numpy array of poses/OpenCV image
            flags (int, optional): zmq flag. Defaults to 0.
            track (bool, optional): zmq flag. Defaults to False.
            copy (bool, optional): zmq flag. Defaults to True.

        """

        md = dict(
            dtype=str(A.dtype),
            shape=A.shape,
            time_send=time.time(),
            time_start_pose_process=self.cam_pose_proc.frame_time[0]

        )
        self.sock.send_json(md, flags=flags)
        return self.sock.send(A, flags, copy=copy, track=track)


def main():

    dlc = ZMQDLCLiveGUI()

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
