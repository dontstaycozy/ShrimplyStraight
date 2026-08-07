try:
    from .popup_manager import show_basic_popup
except ImportError:
    from popup_manager import show_basic_popup

if __name__ == '__main__':
    show_basic_popup()