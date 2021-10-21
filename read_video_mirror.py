import cv2
import os
import sys
import time
from datetime import datetime


ip=sys.argv[1]

RTSP_URL = f'rtsp://{ip}:8554/input'
 
cap = cv2.VideoCapture(RTSP_URL)
fps = cap.get(cv2.CAP_PROP_FPS)

print("FPS: ",fps)

if not cap.isOpened():
    print('Cannot open RTSP stream')
    exit(-1)
 
while True:
    _, frame = cap.read()
    timestamp = cap.get(cv2.CAP_PROP_POS_FRAMES)
    cv2.imshow('RTSP stream', frame)
 
    if cv2.waitKey(1) == ord('q'):
        break
 
cap.release()
cv2.destroyAllWindows()
