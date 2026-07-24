import subprocess
import glob
import os
import random
import threading
import time
from typing import List, Tuple, Optional

import cv2
import mediapipe as mp
import numpy as np
import pystray
from PIL import Image
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from playsound3 import playsound

# --- Constants ---
MODEL_ASSET_PATH = 'pose_landmarker.task'
CALIBRATION_FRAMES_REQUIRED = 30
POSTURE_TOLERANCE_RATIO = 0.97
DEFAULT_ALERT_COOLDOWN = 4
DEFAULT_SOUND_FALLBACK = 'shrimp.mp3'

# MediaPipe Pose Landmark Indices
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12


class PostureMonitor:
    def __init__(self):
        self.running = True
        self.is_calibrated = False
        self.calibration_frames = 0
        self.calibration_ratios: List[float] = []
        self.posture_threshold = 0.0
        self.last_alert_time = time.time()
        self.alert_cooldown = DEFAULT_ALERT_COOLDOWN

        self._setup_landmarker()
        self._load_sounds()

    def _setup_landmarker(self):
        base_options = python.BaseOptions(model_asset_path=MODEL_ASSET_PATH)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def _load_sounds(self):
        self.sound_files = glob.glob("*.mp3")
        if not self.sound_files:
            self.sound_files = [DEFAULT_SOUND_FALLBACK]

    def _calculate_posture_ratio(self, landmarks, frame_shape) -> Optional[float]:
        # Extract pixel coordinates for relevant landmarks
        def get_coords(landmark_idx) -> Tuple[int, int]:
            return (
                int(landmarks[landmark_idx].x * frame_shape[1]),
                int(landmarks[landmark_idx].y * frame_shape[0])
            )

        left_shoulder = get_coords(LEFT_SHOULDER)
        right_shoulder = get_coords(RIGHT_SHOULDER)
        left_ear = get_coords(LEFT_EAR)
        right_ear = get_coords(RIGHT_EAR)

        # Calculate Midpoints
        mid_shoulder = (
            (left_shoulder[0] + right_shoulder[0]) // 2,
            (left_shoulder[1] + right_shoulder[1]) // 2
        )
        mid_ear = (
            (left_ear[0] + right_ear[0]) // 2,
            (left_ear[1] + right_ear[1]) // 2
        )

        # Calculate distances
        neck_length = mid_shoulder[1] - mid_ear[1]
        shoulder_width = np.sqrt(
            (left_shoulder[0] - right_shoulder[0])**2 +
            (left_shoulder[1] - right_shoulder[1])**2
        )

        if shoulder_width == 0:
            shoulder_width = 1  # prevent division by zero

        return neck_length / shoulder_width

    def _process_frame(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        results = self.landmarker.detect(mp_image)

        if not results.pose_landmarks or len(results.pose_landmarks) == 0:
            return

        landmarks = results.pose_landmarks[0]
        posture_ratio = self._calculate_posture_ratio(landmarks, frame.shape)
        
        if posture_ratio is None:
            return

        if not self.is_calibrated:
            self._calibrate(posture_ratio)
        else:
            self._check_posture(posture_ratio)

    def _calibrate(self, posture_ratio: float):
        if self.calibration_frames < CALIBRATION_FRAMES_REQUIRED:
            self.calibration_ratios.append(posture_ratio)
            self.calibration_frames += 1
        else:
            self.posture_threshold = np.mean(self.calibration_ratios) * POSTURE_TOLERANCE_RATIO
            self.is_calibrated = True
            print(f"Calibration complete. Posture threshold: {self.posture_threshold:.2f}")

    def _check_posture(self, posture_ratio: float):
        current_time = time.time()
        
        if posture_ratio < self.posture_threshold:
            if current_time - self.last_alert_time > self.alert_cooldown:
                print(f"Shrimp posture detected! Score: {posture_ratio:.2f}")
                self._play_alert_sound()
                self.last_alert_time = current_time

    def _play_alert_sound(self):
        sound_to_play = random.choice(self.sound_files)
        if os.path.exists(sound_to_play):
            playsound(sound_to_play)

            # Trigger the popup
            subprocess.Popen(["python", "popup.py"])

    def run_camera(self):
        cap = cv2.VideoCapture(0)
        time.sleep(1)  # Warm up camera
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            self._process_frame(frame)
            time.sleep(0.01)

        cap.release()
        self.landmarker.close()

    def stop(self):
        self.running = False


class TrayIconManager:
    def __init__(self, app: PostureMonitor):
        self.app = app
        self.icon = None

    def _create_image(self) -> Image.Image:
        return Image.open("shrimp_icon.png")

    def _on_quit(self, icon, item):
        print("Shutting down ShrimplyStraight...")
        self.app.stop()
        if self.icon:
            self.icon.stop()

    def run(self):
        menu = pystray.Menu(pystray.MenuItem('Quit', self._on_quit))
        self.icon = pystray.Icon("ShrimplyStraight", self._create_image(), "ShrimplyStraight", menu)
        self.icon.run()


def main():
    print("Starting ShrimplyStraight... look at the camera to calibrate!")
    
    app = PostureMonitor()
    tray_manager = TrayIconManager(app)
    
    # Start the camera tracking in a background thread
    camera_thread = threading.Thread(target=app.run_camera, daemon=True)
    camera_thread.start()
    
    # This blocks until the icon is stopped
    tray_manager.run()
    
    # Ensure camera thread cleans up
    camera_thread.join(timeout=1.0)


if __name__ == '__main__':
    main()