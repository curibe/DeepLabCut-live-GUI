import zmq
import time
import numpy as np
import pdb
from datetime import datetime
import pytz
import cv2



def display_frame(frame,pose): 
    """ Display a frame in display window
    """
    display_radius = 3
    display_lik_thresh = 0.5


    if frame is not None:

        img = Image.fromarray(frame)
        if frame.ndim == 3:
            b, g, r = img.split()
            img = Image.merge("RGB", (r, g, b))

       
        if pose is not None:

            im_size = (frame.shape[1], frame.shape[0])

            img_draw = ImageDraw.Draw(img)

            for i in range(pose.shape[0]):
                if pose[i, 2] > display_lik_thresh:
                    try:
                        x0 = (
                            pose[i, 0] - display_radius
                            if pose[i, 0] - display_radius > 0
                            else 0
                        )
                        x1 = (
                            pose[i, 0] + display_radius
                            if pose[i, 0] + display_radius < im_size[1]
                            else im_size[1]
                        )
                        y0 = (
                            pose[i, 1] - display_radius
                            if pose[i, 1] - display_radius > 0
                            else 0
                        )
                        y1 = (
                            pose[i, 1] + display_radius
                            if pose[i, 1] + display_radius < im_size[0]
                            else im_size[0]
                        )
                        coords = [x0, y0, x1, y1]
                        img_draw.ellipse(
                            coords,
                            fill="yellow",
                            outline="yellow",
                        )
                    except Exception as e:
                        print(e)
            


def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    localtime = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = memoryview(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])

    return localtime, md["time_send"], md["time_start_pose_process"], A.reshape(md['shape'])

def store_poses_in_dict(poses_dict,pose,i):
    poses_dict.update({f"{i}":poses})
    

# url = "tcp://18.207.138.137:1936"
url = "tcp://localhost:1936"
ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect(url)
sock.subscribe("") # Subscribe to all topics

# Video stage


print("Starting receiver loop ...")
i = 0
while True:
    print("while")
    localtime, timesend, time_pose_process, poses = recv_array(sock)
    
    cv2.imshow("Frame",poses)
    if cv2.waitKey(2) & 0xff ==ord('q'):
            break

    timesend = datetime.fromtimestamp(timesend)
    time_pose_process = datetime.fromtimestamp(time_pose_process)
    
    delta_time = timesend-time_pose_process
    
    localtime = datetime.strptime(localtime,'%Y-%m-%d %H:%M:%S.%f')
    
    print("localtime(t2): ", localtime, 
    "timesend(t1): ",timesend.strftime('%Y-%m-%d %H:%M:%S.%f'), 
    "time_start_pose(t3)",time_pose_process.strftime('%Y-%m-%d %H:%M:%S.%f'),
    "diff: ", delta_time
    )
    i = i+1
    # print(poses)
    # print("Received array: ",msg)
cv2.destroyAllWindows()
sock.close()
ctx.term()