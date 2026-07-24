import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np
import time
from playsound3 import playsound
import os

# Configure the PoseLandmarker
base_options = python.BaseOptions(model_asset_path='pose_landmarker.task')
options = vision.PoseLandmarkerOptions(
    base_options=base_options,
    output_segmentation_masks=False)
landmarker = vision.PoseLandmarker.create_from_options(options)

cap = cv2.VideoCapture(0)

is_calibrated = False
calibration_frames = 0
calibration_ratios = []
posture_threshold = 0
last_alert_time = time.time()
alert_cooldown = 4
sound_file = 'shrimp_alert.mp3'

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
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
            cv2.putText(frame, f"Calibrating ShrimplyStraight... {calibration_frames}/30", (10, 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2, cv2.LINE_AA)
        elif not is_calibrated:
            # We trigger a posture alert if their ratio drops to 97% of their upright ratio
            posture_threshold = np.mean(calibration_ratios) * 0.97
            is_calibrated = True
            print(f"Calibration complete. Posture threshold: {posture_threshold:.2f}")

        # Draw visuals: T-shape connecting shoulders and neck to visualize the measurements
        cv2.line(frame, left_shoulder, right_shoulder, (255, 0, 0), 2)
        cv2.line(frame, mid_shoulder, mid_ear, (0, 255, 0), 2)
        
        # Draw circles at the keypoints
        cv2.circle(frame, left_shoulder, 5, (255, 0, 0), -1)
        cv2.circle(frame, right_shoulder, 5, (255, 0, 0), -1)
        cv2.circle(frame, left_ear, 5, (0, 255, 0), -1)
        cv2.circle(frame, right_ear, 5, (0, 255, 0), -1)

        if is_calibrated:
            current_time = time.time()
            # If the current ratio is lower than the threshold, the user is shrimping/slouching
            if posture_ratio < posture_threshold:
                status = "Un-shrimp!! (Poor Posture)"
                color = (0, 0, 255)  
                if current_time - last_alert_time > alert_cooldown:
                    print("Shrimp posture detected! Please sit up straight.")
                    if os.path.exists(sound_file):
                        playsound(sound_file)
                    last_alert_time = current_time
            else:
                status = "Shrimply Straight!"
                color = (0, 255, 0)  

            cv2.putText(frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
            cv2.putText(frame, f"Posture Score: {posture_ratio:.2f}/{posture_threshold:.2f}", (10, 60), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)

    cv2.imshow('ShrimplyStraight', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
landmarker.close()
cv2.destroyAllWindows()