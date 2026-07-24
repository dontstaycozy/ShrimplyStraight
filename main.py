import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from playsound3 import playsound
import os
import threading
import pystray
from PIL import Image, ImageDraw
import glob
import random

# Configure the PoseLandmarker
base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False)
landmarker = vision.PoseLandmarker.create_from_options(options)

# Global control variables
running = True
is_calibrated = False
calibration_frames = 0
calibration_ratios = []
posture_threshold = 0
last_alert_time = time.time()
alert_cooldown = 4

# Gather all MP3 files in the current folder
sound_files = glob.glob("*.mp3")
if not sound_files:
    # Fallback just in case
    sound_files = ['shrimp_alert.mp3']

def run_camera():
    global running, is_calibrated, calibration_frames, calibration_ratios, posture_threshold, last_alert_time
    
    cap = cv2.VideoCapture(0)
    
    # Let the camera warm up
    time.sleep(1)
    
    while running and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = landmarker.detect(mp_image)

        if results.pose_landmarks and len(results.pose_landmarks) > 0:
            landmarks = results.pose_landmarks[0]

            # Landmark indices: 11 = Left Shoulder, 12 = Right Shoulder, 7 = Left Ear, 8 = Right Ear
            left_shoulder = (int(landmarks[11].x * frame.shape[1]),
                             int(landmarks[11].y * frame.shape[0]))
            right_shoulder = (int(landmarks[12].x * frame.shape[1]),
                              int(landmarks[12].y * frame.shape[0]))
            left_ear = (int(landmarks[7].x * frame.shape[1]),
                        int(landmarks[7].y * frame.shape[0]))
            right_ear = (int(landmarks[8].x * frame.shape[1]),
                         int(landmarks[8].y * frame.shape[0]))

            # Calculate Midpoints
            mid_shoulder = (int((left_shoulder[0] + right_shoulder[0]) / 2),
                            int((left_shoulder[1] + right_shoulder[1]) / 2))
            mid_ear = (int((left_ear[0] + right_ear[0]) / 2),
                       int((left_ear[1] + right_ear[1]) / 2))

            # Calculate distances for front-facing posture
            # Vertical distance from ears to shoulders (neck length)
            neck_length = mid_shoulder[1] - mid_ear[1]
            
            # Horizontal distance between shoulders (shoulder width)
            shoulder_width = np.sqrt((left_shoulder[0] - right_shoulder[0])**2 + (left_shoulder[1] - right_shoulder[1])**2)
            if shoulder_width == 0:
                shoulder_width = 1  # prevent division by zero
                
            posture_ratio = neck_length / shoulder_width

            if not is_calibrated and calibration_frames < 30:
                calibration_ratios.append(posture_ratio)
                calibration_frames += 1
            elif not is_calibrated:
                # We trigger a posture alert if their ratio drops to 97% of their upright ratio
                posture_threshold = np.mean(calibration_ratios) * 0.97
                is_calibrated = True
                print(f"Calibration complete. Posture threshold: {posture_threshold:.2f}")

            if is_calibrated:
                current_time = time.time()
                # If the current ratio is lower than the threshold, the user is shrimping/slouching
                if posture_ratio < posture_threshold:
                    if current_time - last_alert_time > alert_cooldown:
                        print(f"Shrimp posture detected! Score: {posture_ratio:.2f}")
                        # Pick a random sound from our list
                        sound_to_play = random.choice(sound_files)
                        if os.path.exists(sound_to_play):
                            playsound(sound_to_play)
                        last_alert_time = current_time

        # Sleep briefly to reduce CPU usage since we don't have cv2.waitKey blocking
        time.sleep(0.01)

    cap.release()

def create_image():
    # If there is a custom icon.png in the folder, use it!
    if os.path.exists("shrimp_icon.png"):
        return Image.open("shrimp_icon.png")
        
    # Otherwise, generate a simple shrimp-colored icon for the system tray
    image = Image.new('RGB', (64, 64), color=(255, 127, 80))
    dc = ImageDraw.Draw(image)
    # Draw a white circle
    dc.ellipse((16, 16, 48, 48), fill=(255, 255, 255))
    # Draw a smaller shrimp-colored inner circle
    dc.ellipse((24, 24, 40, 40), fill=(255, 127, 80))
    return image

def on_quit(icon, item):
    global running
    print("Shutting down ShrimplyStraight...")
    running = False
    icon.stop()

def main():
    print("Starting ShrimplyStraight... look at the camera to calibrate!")
    
    # Start the camera tracking in a background thread
    camera_thread = threading.Thread(target=run_camera, daemon=True)
    camera_thread.start()
    
    # Set up the system tray icon
    menu = pystray.Menu(pystray.MenuItem('Quit', on_quit))
    icon = pystray.Icon("ShrimplyStraight", create_image(), "ShrimplyStraight", menu)
    
    # This blocks until the icon is stopped
    icon.run()
    
    landmarker.close()

if __name__ == '__main__':
    main()