#!/bin/bash

ip=${1:-localhost}
option=${2:-notime}
fps=${3:-60}

if [[ $option == "time" ]]; then
    ffmpeg -re -stream_loop -1 -i dog_clip.avi -r $fps \
    -vf "settb=AVTB,setpts='trunc(PTS/1K)*1K+st(1,trunc(RTCTIME/1K))-1K*trunc(ld(1)/1K)',drawtext=text='%{localtime}.%{eif\:1M*t-1K*trunc(t*1K)\:d\:3}':fontsize=27:fontcolor=yellow:x=(w-text_w):y=(h-text_h)" \
    -s 200x200 -f rtsp rtsp://$ip:8554/input
fi 

if [[ $option == "notime" ]]; then
    ffmpeg -re -stream_loop -1 -i dog_clip.avi -r $fps \
    -s 200x200 -f rtsp rtsp://$ip:8554/input
fi

if [[ $option == "nframe" ]]; then
    ffmpeg -re -stream_loop -1 -i dog_clip.avi -r $fps \
    -vf "drawtext=fontfile=Arial.ttf:text='%{frame_num}':start_number=1:x=(w-tw):y=(h-th):fontcolor=yellow:fontsize=50" \
    -s 200x200 -an -f rtsp rtsp://$ip:8554/input
fi

if [[ $option == "frametime" ]]; then
    ffmpeg -re -stream_loop -1 -i dog_clip.avi -r $fps \
    -vf "settb=AVTB,setpts='trunc(PTS/1K)*1K+st(1,trunc(RTCTIME/1K))-1K*trunc(ld(1)/1K)',drawtext=text='%{localtime}.%{eif\:1M*t-1K*trunc(t*1K)\:d\:3}':fontsize=27:fontcolor=yellow:x=(w-text_w):y=(h-text_h),drawtext=text='%{frame_num}':start_number=1:x=1:y=1:fontcolor=yellow:fontsize=50" \
    -s 200x200 -an -f rtsp rtsp://$ip:8554/input
fi

