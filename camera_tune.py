import cv2
from picamera2 import Picamera2

# Initialize the camera
picam2 = Picamera2()

print("Starting the camera...")
picam2.start()

try:
    while True:
        # Capture a frame
        frame = picam2.capture_array()

        # Display the frame
        cv2.imshow("Camera Live Feed", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    # Release resources
    picam2.stop()
    cv2.destroyAllWindows()
    print("Camera stopped.")