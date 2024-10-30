

"""
This script captures images at specified intervals using the Picamera2 on a Raspberry Pi, 
saves them to a directory, and uploads them to a Git repository. It also manages disk usage 
by deleting the local images after they have been successfully pushed to GitHub, ensuring 
that the Raspberry Pi's storage does not get full.

Features:
- Captures images at user-defined intervals.
- Saves images and metadata to a specified directory.
- Automatically creates a metadata CSV file and a README file in the output directory.
- Uses the current Git branch to commit and push images and metadata to the repository.
- Deletes local images after successful upload to GitHub to manage disk space.
- Includes a function to check disk usage and delete the oldest files if the usage exceeds a specified threshold.

Dependencies:
- picamera2
- OpenCV
- Git
- shutil

To use on a Raspberry pi via ssh
1. Log into SSH of the raspberry pi
2. Run the following command:
    nohup python3 pi-camera.py > output.log 2>&1 &
    This prevents the script from stopping when the SSH session is closed.
    The output of the script is written to output.log.
3. To stop the script, find the process ID (PID) using the following command:
    ps -ef | grep pi-camera.py
    and then kill the process using:
    kill <PID>

"""
import time
import os
import subprocess
import cv2
from picamera2 import Picamera2, Picamera2Error
import shutil
import argparse

def manage_disk_usage(directory, threshold=80):
    total, used, free = shutil.disk_usage("/")
    used_percentage = (used / total) * 100

    if used_percentage > threshold:
        print("Disk usage exceeded threshold. Deleting oldest files...")
        files = sorted(
            (os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".jpg")),
            key=os.path.getctime
        )
        while used_percentage > threshold and files:
            oldest_file = files.pop(0)
            os.remove(oldest_file)
            print(f"Deleted {oldest_file}")
            total, used, free = shutil.disk_usage("/")
            used_percentage = (used / total) * 100

parser = argparse.ArgumentParser(description="Capture images at specified intervals using the Picamera2.")
parser.add_argument("experiment_name", type=str, help="Name of the experiment")
parser.add_argument("image_interval", type=int, help="Image capture interval in seconds")
args = parser.parse_args()

experiment_name = args.experiment_name
image_interval = args.image_interval

try:
    picam2 = Picamera2()
    picam2.start()
except Picamera2Error as e:
    print(f"Failed to initialize Picamera2: {e}")
    exit(1)

timestamp = time.strftime("%Y%m%d-%H%M%S")
output_dir = f"images/{experiment_name}_{timestamp}"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

metadata_path = os.path.join(output_dir, 'metadata.csv')
readme_path = os.path.join(output_dir, 'README.md')

if not os.path.exists(metadata_path):
    with open(metadata_path, 'w') as f:
        f.write("Timestamp,Image Path\n")

if not os.path.exists(readme_path):
    with open(readme_path, 'w') as f:
        f.write(f"# {experiment_name} Images\n\n")
        f.write("This directory contains images captured during the experiment.\n")
        f.write("Each image is named with a timestamp indicating when it was taken.\n\n")
        f.write("## Metadata\n\n")
        f.write("Additional metadata about the images can be found in `metadata.csv`.\n")

repo_path = os.path.dirname(os.path.abspath(__file__))
current_branch = subprocess.run(['git', 'branch', '--show-current'], cwd=repo_path, capture_output=True, text=True).stdout.strip()
subprocess.run(['git', 'checkout', current_branch], cwd=repo_path)

interval = image_interval
while True:
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    image_path = os.path.join(output_dir, f"{timestamp}.jpg")

    try:
        frame = picam2.capture_array()
        frame = cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        cv2.imwrite(image_path, frame)
    except Exception as e:
        print(f"Failed to capture or save image: {e}")
        continue

    with open(metadata_path, 'a') as f:
        f.write(f"{timestamp},{image_path}\n")

    subprocess.run(['git', 'add', image_path, metadata_path], cwd=repo_path)
    subprocess.run(['git', 'commit', '-m', f"Add image and metadata for {timestamp}"], cwd=repo_path)
    subprocess.run(['git', 'push'], cwd=repo_path)

    print(f"Captured and uploaded image at {timestamp}")

    os.remove(image_path)
    print(f"Deleted local image at {image_path}")

    manage_disk_usage(output_dir)

    time.sleep(interval)

picam2.stop()
print("Camera stopped.")