from dlclivegui import camera
from dlclivegui import DLCLiveGUI
from tkinter import StringVar,BooleanVar,Tk
from PIL import Image, ImageTk, ImageDraw
from datetime import datetime
import numpy as np
import time
import zmq
import pytz
import pdb 

class RTMPDLCLIVEGUI(DLCLiveGUI):

    def __init__(self):
        url = "tcp://*:1936"
        self.ctxzmq = zmq.Context()    
        self.sock = self.ctxzmq.socket(zmq.PUB)
        self.sock.bind(url)


        
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
                    
                    self.send_numpy_array_by_zmq(pose)
                    

                # imgtk = ImageTk.PhotoImage(image=img)
                # self.display_frame_label.imgtk = imgtk
                # self.display_frame_label.configure(image=imgtk)

            self.display_frame_label.after(10, self.display_frame)

    def send_numpy_array_by_zmq(self, pose):

        if pose is not None:
            # write to pipe
            print("sending o zmq:",pose)
            self.send_array(pose, copy=False)
    def send_array(self, A, flags=0,track=False, copy=True):
        md = dict(
            dtype = str(A.dtype),
            shape = A.shape,
            timeshot = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

        )
        self.sock.send_json(md,flags=flags)
        return self.sock.send(A,flags,copy=copy, track=track)


def main():

    dlc=RTMPDLCLIVEGUI()

    # set options setted in gui
    dlc.dlc_option = StringVar(value="dlclive-test")
    dlc.display_keypoints = BooleanVar(value=True)
    dlc.change_display_keypoints()

    print("Init cam...")
    dlc.init_cam()
    
    print("Running dlc analyse...")
    dlc.init_dlc()

    dlc.run()

if __name__ == "__main__":
    main()