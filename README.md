# ShrimplyStraight

ShrimplyStraight is a small Python desktop utility that uses your webcam and MediaPipe Pose Landmarker to detect poor posture and play an alert sound when the user starts to "shrimp" or slouch.

## What it does

- Tracks shoulder and ear landmarks from the webcam feed
- Calibrates a posture baseline during startup
- Detects slouching/posture drift by comparing the current neck-to-shoulder ratio against the calibrated threshold
- Alerts the user with a random `.mp3` sound file from the project folder
- Runs quietly in the system tray for background use

## Features

- Real-time pose estimation using MediaPipe
- Automatic calibration over the first 30 frames
- Sound-based posture alerts with cooldown protection
- Simple system tray controls with a Quit action
- Fallback icon generation if no custom icon image is provided

## Requirements

Before running this project, install the following Python dependencies:

```bash
pip install opencv-python mediapipe playsound3 pystray pillow numpy
```

You will also need:

- A webcam connected to your computer
- A `.task` model file named `pose_landmarker.task` in the project folder
- One or more `.mp3` files in the project folder for alert sounds

## Project structure

```text
ShrimplyStraight/
├── main.py
├── pose_landmarker.task
├── README.md
└── *.mp3
```

## How it works

1. The application starts the camera feed in a background thread.
2. It calibrates the user's neutral upright posture for the first 30 detection frames.
3. Once calibrated, it calculates a posture ratio from the distance between the ears and shoulders.
4. If the ratio falls below the threshold for long enough, it plays a random alert sound.
5. The app stays running in the system tray until you choose Quit.

## Running the application

From the project directory, run:

```bash
python main.py
```

## Notes

- The alert sound is chosen randomly from all `.mp3` files found in the current folder.
- If no sound file is found, the program falls back to `shrimp.mp3` if present.
- The posture threshold is based on a 97% ratio drop from the user's calibrated upright posture.

## License

This project is provided as-is for personal and educational use.

