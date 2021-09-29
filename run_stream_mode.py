from dlclivegui import camera
from dlclivegui import DLCLiveGUI
from tkinter import StringVar,BooleanVar,Tk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
import subprocess
import pdb 

class RTMPDLCLIVEGUI(DLCLiveGUI):

    def __init__(self):
        rtmp_url = "rtsp://localhost:8554/mystream2"

        # command and params for ffmpeg
        command = ['ffmpeg',
                '-y',
                '-f', 'rawvideo',
                '-vcodec', 'rawvideo',
                '-pix_fmt', 'rgb24',
                '-s', "{}x{}".format(200, 200),
                '-r', '30',
                '-i', '-',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-preset', 'ultrafast',
                '-f', 'rtsp',
                rtmp_url]
        self.p = subprocess.Popen(command, stdin=subprocess.PIPE)
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
                    lastimg = np.asarray(img)
                    self.send_numpy_frame_to_ffmpeg(lastimg)

                imgtk = ImageTk.PhotoImage(image=img)
                self.display_frame_label.imgtk = imgtk
                self.display_frame_label.configure(image=imgtk)

            self.display_frame_label.after(10, self.display_frame)

    def send_numpy_frame_to_ffmpeg(self,frame):

        if frame is not None:
            # write to pipe
            self.p.stdin.write(frame.tobytes())


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