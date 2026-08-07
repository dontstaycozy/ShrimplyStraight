try:
    from .popup_manager import show_image_popup
except ImportError:
    from popup_manager import show_image_popup

if __name__ == '__main__':
    show_image_popup("assets/images/whale.jpg", "You're shrimping!", "I will fix my posture!")
