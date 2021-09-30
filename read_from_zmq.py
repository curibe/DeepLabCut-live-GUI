import zmq
import time
import numpy as np
import pdb
from datetime import datetime
import pytz


def recv_array(socket, flags=0, copy=True, track=False):
    """recv a numpy array"""
    md = socket.recv_json(flags=flags)
    mytime = datetime.now(pytz.timezone('America/Bogota')).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    msg = socket.recv(flags=flags, copy=copy, track=track)
    buf = memoryview(msg)
    A = np.frombuffer(buf, dtype=md['dtype'])

    return mytime, md["timeshot"], A.reshape(md['shape'])

ctx = zmq.Context()
sock = ctx.socket(zmq.SUB)
sock.connect("tcp://127.0.0.1:1936")
sock.subscribe("") # Subscribe to all topics

print("Starting receiver loop ...")
while True:
    mytime, timeshot,msg = recv_array(sock)
    t1 = datetime.strptime(timeshot,'%Y-%m-%d %H:%M:%S.%f')
    t2 = datetime.strptime(mytime,'%Y-%m-%d %H:%M:%S.%f')
    print(mytime, timeshot, (t2-t1).total_seconds())
    # print("Received array: ",msg)

sock.close()
ctx.term()