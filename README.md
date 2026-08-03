# ShrimplyStraight

ShrimplyStraight is a small Python desktop utility that uses your webcam and MediaPipe Pose Landmarker to detect poor posture and play an alert sound when the user starts to "shrimp" or slouch.

## What it does

- Tracks shoulder and ear landmarks from the webcam feed.
- Calibrates a posture baseline during startup.
- Detects slouching/posture drift by comparing the current neck-to-shoulder ratio against the calibrated threshold.
- Alerts the user with a random `.mp3` sound file and various interactive popups!
- Runs quietly in the system tray for background use.

## Features

- **Real-time pose estimation** using MediaPipe.
- **Automatic calibration** over the first 30 frames.
- **Dynamic visual popups** when you slouch, including basic alerts, image warnings (whale and krill), and even taking a quick snapshot to expose your shrimp posture! (The snapshot is kept purely in memory and immediately deleted from your disk to save space).
- **Weighted randomness** for popups so that different alerts appear with varying rarity.
- **Sound-based posture alerts** with cooldown protection.
- **Simple system tray controls** to toggle sounds and popups, dismiss/close all open popups at once, and a clean Quit action that safely closes all active popups.

## Requirements

Before running this project, install the following Python dependencies:

```bash
pip install opencv-python mediapipe playsound3 pystray pillow numpy
```

You will also need:
- A webcam connected to your computer.

## Project Structure

The project has been carefully organized to keep assets and sub-scripts separated:

```text
ShrimplyStraight/
├── Start_Shrimply.vbs       # Core script executor
├── ShrimplyStraight.lnk     # Double-click this shortcut to start!
├── main.py                  # Main application logic
├── README.md
├── popups/                  # Visual popup scripts
│   ├── popup.py
│   ├── picture_popup.py
│   ├── image_popup1.py
│   └── image_popup2.py
└── assets/
    ├── images/              # Icons and popup images (shrimp_icon.png, krill.jpg, whale.jpg)
    ├── audio/               # Alert sounds (*.mp3)
    └── models/              # MediaPipe model (pose_landmarker.task)
```

## How it works

1. The application starts the camera feed in a background thread.
2. It calibrates the user's neutral upright posture for the first 30 detection frames.
3. Once calibrated, it calculates a posture ratio from the distance between the ears and shoulders.
4. If the ratio falls below the threshold for long enough, it triggers an alert sound and a random popup.
5. The app stays running in the system tray until you choose Quit, closing any lingering popups.

## Running the application

You can simply double-click the **`ShrimplyStraight`** shortcut to launch the application quietly in the background!

Alternatively, you can run it from the command line:
```bash
python main.py
```

## Notes

- The alert sound is chosen randomly from all `.mp3` files found in the `assets/audio/` folder.
- If no sound file is found, the program falls back to `shrimp.mp3` if present.
- The posture threshold is based on a 97% ratio drop from the user's calibrated upright posture.

## License

This project is provided as-is for personal and educational use.
