from datetime import datetime
from threading import Thread

import cv2
import numpy as np
import pytz
import zmq


class CountsPerSec:
    """
    Class that tracks the number of occurrences ("counts") of an
    arbitrary event and returns the frequency in occurrences
    (counts) per second. The caller must increment the count.
    """

    def __init__(self):
        self._start_time = None
        self._num_occurrences = 0

    def start(self):
        self._start_time = datetime.now()
        return self

    def increment(self):
        self._num_occurrences += 1

    def countsPerSec(self):
        elapsed_time = (datetime.now() - self._start_time).total_seconds()
        return self._num_occurrences / elapsed_time if elapsed_time > 0 else 0


class VideoShow:
    """
    Class that continuously shows a frame using a dedicated thread.
    """

    def __init__(self, frame=None):
        self.frame = frame
        self.stopped = False

    def start(self):
        Thread(target=self.show, args=()).start()
        return self

    def show(self):
        while not self.stopped:
            cv2.imshow("Video", self.frame)
            if cv2.waitKey(1) == ord("q"):
                self.stopped = True

    def stop(self):
        self.stopped = True


def putIterationsPerSec(frame, iterations_per_sec):
    """
    Add iterations per second text to lower-left corner of a frame.
    """

    cv2.putText(frame, "{:.0f} iterations/sec".format(iterations_per_sec),
        (10, 450), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255))
    return frame


def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    localtime = datetime.now(pytz.timezone('America/Bogota'))
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = memoryview(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])

    return localtime, md["time_send"], md["time_start_pose_process"], A.reshape(md['shape'])


def get_frame(sock):
    while True:

        localtime, timesend, time_pose_process, poses = recv_array(sock)

        timesend = datetime.fromtimestamp(timesend)
        time_pose_process = datetime.fromtimestamp(time_pose_process)

        delta_time = timesend-time_pose_process
        previous = localtime
        yield (True, poses)


class VideoGet:
    """
    Class that continuously gets frames from a VideoCapture object
    with a dedicated thread.
    """

    def __init__(self, sock=''):
        self.stream = get_frame(sock)
        (self.grabbed, self.frame) = next(self.stream)
        self.stopped = False

    def start(self):
        Thread(target=self.get, args=()).start()
        return self

    def get(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = next(self.stream)

    def stop(self):
        self.stopped = True


def threadBoth(source=0):
    """
    Dedicated thread for grabbing video frames with VideoGet object.
    Dedicated thread for showing video frames with VideoShow object.
    Main thread serves only to pass frames between VideoGet and
    VideoShow objects/threads.
    """
    video_getter = VideoGet(source).start()
    video_shower = VideoShow(video_getter.frame).start()
    cps = CountsPerSec().start()
    while True:
        if video_getter.stopped or video_shower.stopped:
            video_shower.stop()
            video_getter.stop()
            break

        frame = video_getter.frame
        frame = putIterationsPerSec(frame, cps.countsPerSec())
        video_shower.frame = frame
        cps.increment()


class SubscriberClient():
    """docstring for SubscriberClient."""
    def __init__(self, ip="localhost", url=""):

        self.url = url if url else f"tcp://{ip}:1936"
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.SUB)

    def start(self, topic=""):
        self.socket.connect(self.url)
        self.socket.subscribe(topic)

    def recv_array(self, flags=0, copy=True, track=False):
        """recv a numpy array"""
        md = self.socket.recv_json(flags=flags)

        localtime = datetime.now(pytz.timezone('America/Bogota'))
        msg = self.socket.recv(flags=flags, copy=copy, track=track)
        buf = memoryview(msg)
        A = np.frombuffer(buf, dtype=md['dtype'])

        return A.reshape(md['shape']), localtime, md["time_send"], md["time_start_pose_process"], 

    def get_poses(self):
        print("Starting receive poses ...")
        while True:
            poses, localtime, timesend, time_pose_process = self.recv_array()
            yield poses

    def get_frames(self):
        print("Starting receive frames ...")
        threadBoth(self.socket)

    def end(self):
        self.socket.close()
        self.ctx.term()


def main():
    receive = "video"
    client = SubscriberClient()
    client.start()

    if receive == "poses":
        for pose in client.get_poses():
            print("pose: ", pose)
    elif receive == "video":
        client.get_frames()

    else:
        print("no options")

    client.end()


if __name__ == "__main__":
    main()

