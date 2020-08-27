import cv2
import numpy as np
import time

# Define the source as shared memory (shmsrc) and point to the socket. !
# Set the caps (raw (not encoded) frame video/x-raw, format as BGR or RGB (opencv format of grabbed cameras)) and define the properties of the camera !
# And sink the grabbed data to the appsink

################################# sender #################################

# sender
"""sh
gst-launch-1.0 -v videotestsrc is-live=true \
    ! 'video/x-raw,width=1920,height=1080,format=(string)BGR,framerate=60/1' \
    ! videoconvert \
    ! shmsink socket-path=/tmp/foo name=/tmp/shm sync=true wait-for-connection=false shm-size=160000000
"""


################################# receiver #################################

# receiver 
# ! note, shmsrc's `width/heigth/format` match shmsink
"""sh
gst-launch-1.0 -v shmsrc do-timestamp=true socket-path=/tmp/foo name=/tmp/shm \
    ! 'video/x-raw,width=1920,height=1080,format=(string)BGR,framerate=60/1' \
    ! videoconvert \
    ! fpsdisplaysink text-overlay=false sync=false -e
"""

# define receiver to the up point
frame_rate = 60
frame_width = 1920
frame_height = 1080

# The `sync` and `drop` options here instruct Gstreamer to not block the program waiting for new frames and to drop
# frames if OpenCV cannot read them quickly enough.
# Or you can run the capture in a seperate thread and run a another thread to do heavy job
cap = cv2.VideoCapture(f"shmsrc do-timestamp=true socket-path=/tmp/foo name=/tmp/shm ! video/x-raw, format=BGR, width={frame_width}, height={frame_height}, framerate={frame_rate}/1 ! videoconvert ! appsink sync=false drop=true")

if not cap.isOpened():
    print("Cannot capture from camera. Exiting.")
    quit()

tic = time.time()
# Loop it
try:
    while True:
        ret, frame = cap.read()
        #
        if ret == False:
            break
        #print(frame.shape, frame[892][189])
        cv2.imshow("frame", cv2.resize(frame, (1280, 720)))
        #np.sum(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        toc = time.time()
        print(f"fps: {1/(toc-tic)}, frame number: {cap.get(cv2.CAP_PROP_POS_FRAMES)}, frame_width: {cap.get(cv2.CAP_PROP_FRAME_WIDTH)}, frame_height: {cap.get(cv2.CAP_PROP_FRAME_HEIGHT)}, fps: {cap.get(cv2.CAP_PROP_FPS)}, total_frame: {cap.get(cv2.CAP_PROP_FRAME_COUNT)}")
        tic = toc

except KeyboardInterrupt:
    print(f"exit while true loop")

cap.release()