import ctypes
import glob
import multiprocessing
import os
import random
import subprocess
import sys
import tempfile
import threading
import time
from typing import Callable, List, Optional, Tuple

import cv2
import mediapipe as mp
import numpy as np
import pystray
from PIL import Image
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from playsound3 import playsound


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    # PyInstaller creates a temp folder and stores path in _MEIPASS
    if hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path

    # Check relative to executable location (when running as standalone EXE)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        local_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(local_path):
            return local_path

    # Check relative to this script file (dev mode)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_path = os.path.join(script_dir, relative_path)
    if os.path.exists(local_path):
        return local_path

    return os.path.abspath(relative_path)


# --- Posture & Alert Constants ---
CALIBRATION_FRAMES_REQUIRED = 35   # ~1.2 seconds of camera frames to establish baseline
POSTURE_TOLERANCE_RATIO = 0.90      # Posture below 90% of baseline counts as slouching
SLOUCH_CONFIRM_SECONDS = 0.4       # Triggers fast (0.4s) every time user slouches
CONTINUOUS_SLOUCH_REMINDER_COOLDOWN = 5   # While continuously slouching, spams more popups every 5s!

# MediaPipe Pose Landmark Indices
LEFT_EAR = 7
RIGHT_EAR = 8
LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12


class PostureMonitor:
    def __init__(self):
        self.running = True
        self.sound_enabled = True
        self.popups_enabled = True
        self.is_calibrated = False
        self.calibration_frames = 0
        self.calibration_ratios: List[float] = []
        self.posture_threshold = 0.0
        self.last_alert_time = 0.0
        self.is_slouching = False
        self.slouch_start_time: Optional[float] = None
        self.active_popups: List[subprocess.Popen] = []

        # Callbacks for UI/Tray notifications
        self.on_calibration_complete: Optional[Callable[[float], None]] = None
        self.on_recalibration_start: Optional[Callable[[], None]] = None

        self._setup_landmarker()
        self._load_sounds()

    def _setup_landmarker(self):
        model_path = get_resource_path('assets/models/pose_landmarker.task')
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.PoseLandmarkerOptions(
            base_options=base_options,
            output_segmentation_masks=False
        )
        self.landmarker = vision.PoseLandmarker.create_from_options(options)

    def _load_sounds(self):
        sound_patterns = [
            get_resource_path("assets/audio/*.mp3"),
            os.path.join(os.path.dirname(sys.executable), "assets", "audio", "*.mp3"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "audio", "*.mp3"),
            "assets/audio/*.mp3"
        ]

        found_sounds = set()
        for pattern in sound_patterns:
            for s in glob.glob(pattern):
                if os.path.exists(s):
                    found_sounds.add(os.path.abspath(s))

        self.sound_files = list(found_sounds)
        if not self.sound_files:
            fallback = get_resource_path('assets/audio/shrimp.mp3')
            if os.path.exists(fallback):
                self.sound_files = [fallback]

    def request_recalibration(self):
        """Reset calibration state to measure new baseline posture."""
        self.is_calibrated = False
        self.calibration_frames = 0
        self.calibration_ratios.clear()
        self.is_slouching = False
        self.slouch_start_time = None
        if self.on_recalibration_start:
            self.on_recalibration_start()

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
            # When user is not visible, reset slouch tracker
            self.is_slouching = False
            self.slouch_start_time = None
            return

        landmarks = results.pose_landmarks[0]
        posture_ratio = self._calculate_posture_ratio(landmarks, frame.shape)
        
        if posture_ratio is None:
            self.is_slouching = False
            self.slouch_start_time = None
            return

        if not self.is_calibrated:
            self._calibrate(posture_ratio)
        else:
            self._check_posture(posture_ratio, frame)

    def _calibrate(self, posture_ratio: float):
        if self.calibration_frames < CALIBRATION_FRAMES_REQUIRED:
            self.calibration_ratios.append(posture_ratio)
            self.calibration_frames += 1
        else:
            self.posture_threshold = np.mean(self.calibration_ratios) * POSTURE_TOLERANCE_RATIO
            self.is_calibrated = True
            print(f"Calibration complete. Posture threshold: {self.posture_threshold:.2f}")
            if self.on_calibration_complete:
                self.on_calibration_complete(self.posture_threshold)

    def _check_posture(self, posture_ratio: float, frame):
        current_time = time.time()
        
        if posture_ratio < self.posture_threshold:
            # User is currently in slouching posture
            if self.slouch_start_time is None:
                self.slouch_start_time = current_time
            elif (current_time - self.slouch_start_time) >= SLOUCH_CONFIRM_SECONDS:
                if not self.is_slouching:
                    # Brand new slouch event detected! Trigger immediately every time!
                    self.is_slouching = True
                    self.last_alert_time = current_time
                    print(f"🦐 Slouch detected! Score: {posture_ratio:.2f} (Threshold: {self.posture_threshold:.2f})")
                    self._trigger_alert(frame)
                else:
                    # User is still slouched continuously; repeat alert periodically if uncorrected
                    if (current_time - self.last_alert_time) >= CONTINUOUS_SLOUCH_REMINDER_COOLDOWN:
                        self.last_alert_time = current_time
                        print(f"🦐 Still slouching! Score: {posture_ratio:.2f}")
                        self._trigger_alert(frame)
        else:
            # Posture is good/upright! Instantly reset slouch state so the next slouch triggers immediately
            if self.is_slouching:
                print(f"✅ Good posture restored! (Score: {posture_ratio:.2f})")
            self.is_slouching = False
            self.slouch_start_time = None

    def _trigger_alert(self, frame):
        # 1. Play sound alert
        if self.sound_enabled and self.sound_files:
            sound_to_play = random.choice(self.sound_files)
            if os.path.exists(sound_to_play):
                try:
                    playsound(sound_to_play, block=False)
                except Exception as e:
                    print(f"Error playing sound: {e}")

        # 2. Launch popup alert (spams popups every time triggered!)
        if self.popups_enabled:
            # Clean up dead popups from tracking list
            self.active_popups = [p for p in self.active_popups if p.poll() is None]

            # Choose varied popup types: basic (40%), picture snap (20%), whale (20%), krill (20%)
            popup_choice = random.choices(['basic', 'picture', 'image1', 'image2'], weights=[40, 20, 20, 20], k=1)[0]
            
            snap_path = None
            if popup_choice == 'picture':
                font = cv2.FONT_HERSHEY_DUPLEX
                text = "CERTIFIED SHRIMP"
                text_size = cv2.getTextSize(text, font, 1.5, 3)[0]
                text_x = (frame.shape[1] - text_size[0]) // 2
                text_y = frame.shape[0] - 50
                cv2.putText(frame, text, (text_x, text_y), font, 1.5, (0, 0, 0), 6, cv2.LINE_AA)
                cv2.putText(frame, text, (text_x, text_y), font, 1.5, (0, 0, 255), 3, cv2.LINE_AA)
                snap_path = os.path.join(tempfile.gettempdir(), f"shrimp_snap_{int(time.time() * 1000)}.jpg")
                cv2.imwrite(snap_path, frame)

            try:
                if getattr(sys, 'frozen', False):
                    # Running as compiled standalone EXE
                    cmd = [sys.executable, "--popup", popup_choice]
                    if snap_path:
                        cmd.append(snap_path)
                else:
                    # Running as Python script
                    pythonw_candidate = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
                    python_bin = pythonw_candidate if os.path.exists(pythonw_candidate) else sys.executable
                    cmd = [python_bin, os.path.abspath(__file__), "--popup", popup_choice]
                    if snap_path:
                        cmd.append(snap_path)

                p = subprocess.Popen(cmd)
                self.active_popups.append(p)
            except Exception as e:
                print(f"Error launching popup: {e}")

    def run_camera(self):
        cap = cv2.VideoCapture(0)
        time.sleep(1)  # Warm up camera
        
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            try:
                self._process_frame(frame)
            except Exception as e:
                print(f"Error processing frame: {e}")
            
            time.sleep(0.01)

        cap.release()
        self.landmarker.close()

    def close_all_popups(self):
        for p in self.active_popups:
            try:
                if p.poll() is None:
                    p.terminate()
            except Exception as e:
                print(f"Error terminating popup: {e}")
        self.active_popups.clear()

    def stop(self):
        self.running = False
        self.close_all_popups()


class TrayIconManager:
    def __init__(self, app: PostureMonitor):
        self.app = app
        self.icon = None

        # Wire up callbacks from monitor to tray notifications
        self.app.on_calibration_complete = self._on_calibration_done
        self.app.on_recalibration_start = self._on_recalibration_begin

    def _create_image(self) -> Image.Image:
        icon_path = get_resource_path("assets/images/shrimp_icon.png")
        if os.path.exists(icon_path):
            return Image.open(icon_path)
        # Fallback 32x32 blank image if icon missing
        return Image.new('RGB', (32, 32), color=(255, 120, 120))

    def notify(self, message: str, title: str = "ShrimplyStraight"):
        """Show a native Windows system tray notification."""
        try:
            if self.icon and hasattr(self.icon, 'notify'):
                self.icon.notify(message, title)
        except Exception as e:
            print(f"Notification error: {e}")

    def _on_calibration_done(self, threshold: float):
        self.notify("✅ Baseline calibrated! Posture monitoring is live.\nStay straight!", "ShrimplyStraight")

    def _on_recalibration_begin(self):
        self.notify("🔄 Recalibrating posture...\nPlease sit up straight for 2 seconds!", "ShrimplyStraight")

    def _recalibrate(self, icon, item):
        self.app.request_recalibration()

    def _close_all_popups(self, icon, item):
        self.app.close_all_popups()

    def _toggle_sound(self, icon, item):
        self.app.sound_enabled = not self.app.sound_enabled

    def _toggle_popups(self, icon, item):
        self.app.popups_enabled = not self.app.popups_enabled

    def _on_quit(self, icon, item):
        print("Shutting down ShrimplyStraight...")
        self.app.stop()
        if self.icon:
            self.icon.stop()

    def run(self):
        menu = pystray.Menu(
            pystray.MenuItem('🔄 Recalibrate Posture', self._recalibrate),
            pystray.MenuItem('🖼️ Close All Popups', self._close_all_popups),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('🔊 Sound Alerts Enabled', self._toggle_sound, checked=lambda item: self.app.sound_enabled),
            pystray.MenuItem('🪟 Visual Popups Enabled', self._toggle_popups, checked=lambda item: self.app.popups_enabled),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem('❌ Quit ShrimplyStraight', self._on_quit)
        )
        self.icon = pystray.Icon("ShrimplyStraight", self._create_image(), "ShrimplyStraight", menu)
        
        # Show startup notification once tray icon loop starts
        def on_icon_ready(icon):
            icon.visible = True
            time.sleep(0.5)
            self.notify("🦐 ShrimplyStraight is active in your tray!\nSit up straight now to calibrate.", "ShrimplyStraight")

        self.icon.run(setup=on_icon_ready)


_single_instance_mutex = None


def acquire_single_instance_lock() -> bool:
    """Ensure only one main instance of ShrimplyStraight runs simultaneously."""
    global _single_instance_mutex
    mutex_name = "Global\\ShrimplyStraight_SingleInstance_Mutex_2026"
    kernel32 = ctypes.windll.kernel32
    _single_instance_mutex = kernel32.CreateMutexW(None, False, mutex_name)
    last_error = kernel32.GetLastError()
    ERROR_ALREADY_EXISTS = 183
    if last_error == ERROR_ALREADY_EXISTS:
        return False
    return True


def main():
    if not acquire_single_instance_lock():
        print("ShrimplyStraight is already running in your system tray!")
        sys.exit(0)

    print("Starting ShrimplyStraight... look at the camera to calibrate!")
    
    app = PostureMonitor()
    tray_manager = TrayIconManager(app)
    
    # Start the camera tracking in a background thread
    camera_thread = threading.Thread(target=app.run_camera, daemon=True)
    camera_thread.start()
    
    # This blocks until the icon is stopped (Quit is clicked)
    tray_manager.run()
    
    # Ensure camera thread cleans up
    camera_thread.join(timeout=1.0)


if __name__ == '__main__':
    multiprocessing.freeze_support()

    # Handle popup subprocess dispatch
    if len(sys.argv) > 1 and sys.argv[1] == "--popup":
        from popups.popup_manager import dispatch_popup
        p_type = sys.argv[2] if len(sys.argv) > 2 else 'basic'
        p_args = sys.argv[3:] if len(sys.argv) > 3 else []
        dispatch_popup(p_type, *p_args)
        sys.exit(0)

    main()