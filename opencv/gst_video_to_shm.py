import time
import cv2

################################# sender #################################

# Cam properties
frame_rate = 60
frame_width = 1920
frame_height = 1080

# Create capture
gst_cap_str = f"videotestsrc ! video/x-raw,width={frame_width},height={frame_height},format=(string)BGR,framerate={frame_rate}/1 ! videoconvert ! appsink"

cap = cv2.VideoCapture(gst_cap_str, cv2.CAP_GSTREAMER)

# Check if cap is open
if cap.isOpened() is not True:
    print("Cannot open video. Exiting.")
    cap.release()
    quit()

# Define the gstreamer sink
gst_out_str = f"appsrc ! videoconvert ! shmsink socket-path=/tmp/foo name=/tmp/shm sync=false wait-for-connection=false shm-size=160000000"

# Create videowriter as a SHM sink
out = cv2.VideoWriter(gst_out_str, cv2.CAP_GSTREAMER, 0, frame_rate, (frame_width, frame_height), True)

# Check if cap is open
if out.isOpened() is not True:
    print("Cannot open out. Exiting.")
    cap.release()
    out.release()
    quit()

# Loop it
try:
    while True:
        # Get the frame
        ret, frame = cap.read()
        # Check
        if ret is True:
            # Flip frame
            frame = cv2.flip(frame, 1)
            # Write to SHM
            out.write(frame)
        else:
            print("Camera error.")
            time.sleep(10)
except KeyboardInterrupt:
    print(f"exit while true loop")

out.release()
cap.release()


################################# receiver #################################

# receiver, 
# ! note, shmsrc's `width/heigth/format` match shmsink
"""sh
gst-launch-1.0 -v shmsrc do-timestamp=true socket-path=/tmp/foo name=/tmp/shm \
    ! 'video/x-raw,width=1920,height=1080,format=(string)BGR,framerate=(fraction)60/1' \
    ! videoconvert \
    ! fpsdisplaysink text-overlay=false sync=false -e
"""