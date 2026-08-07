import sys

try:
    from .popup_manager import show_picture_popup
except ImportError:
    from popup_manager import show_picture_popup

if __name__ == '__main__':
    snap_path = sys.argv[1] if len(sys.argv) > 1 else "shrimp_snap.jpg"
    show_picture_popup(snap_path)
