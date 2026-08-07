import os
import random
import sys
import tkinter as tk
from PIL import Image, ImageTk


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    # Check if bundled inside PyInstaller temp dir
    if hasattr(sys, '_MEIPASS'):
        bundle_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundle_path):
            return bundle_path

    # Check next to executable / script
    base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)))
    local_path = os.path.join(base_dir, relative_path)
    if os.path.exists(local_path):
        return local_path

    # Fallback to current working directory
    return os.path.abspath(relative_path)


def show_basic_popup():
    root = tk.Tk()
    root.attributes('-topmost', True)
    root.overrideredirect(True)

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    x = random.randint(50, max(50, screen_width - 350))
    y = random.randint(50, max(50, screen_height - 250))

    root.geometry(f"300x150+{x}+{y}")

    frame = tk.Frame(root, highlightbackground="#6e0c36", highlightthickness=4, bg='#ff9f9f')
    frame.pack(expand=True, fill='both')

    lbl = tk.Label(
        frame,
        text="🦐 ALERT! 🦐\n\nShrimp DETECTED!\nUn-shrimp yourself immediately!",
        bg='#ff9f9f',
        fg='#6e0c36',
        font=("Helvetica", 11, "bold")
    )
    lbl.pack(expand=True, fill='both', pady=(15, 0))

    btn = tk.Button(
        frame,
        text="I'm sorry, I'll sit up!",
        command=root.destroy,
        bg='white',
        fg='black',
        font=("Helvetica", 9, "bold"),
        cursor="hand2"
    )
    btn.pack(pady=15)

    root.mainloop()


def show_image_popup(image_rel_path: str, caption_text: str, button_text: str):
    image_full_path = get_resource_path(image_rel_path)

    if not os.path.exists(image_full_path):
        # Fallback to basic popup if image not found
        show_basic_popup()
        return

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.overrideredirect(True)

    img = Image.open(image_full_path)
    img.thumbnail((400, 400))
    width, height = img.size

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    window_width = width + 20
    window_height = height + 110

    max_x = screen_width - window_width - 50
    max_y = screen_height - window_height - 50
    x = random.randint(50, max_x) if max_x >= 50 else 50
    y = random.randint(50, max_y) if max_y >= 50 else 50

    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    frame = tk.Frame(root, highlightbackground="#6e0c36", highlightthickness=4, bg='#ff9f9f')
    frame.pack(expand=True, fill='both')

    photo = ImageTk.PhotoImage(img)
    lbl_img = tk.Label(frame, image=photo, bg='#ff9f9f')
    lbl_img.image = photo
    lbl_img.pack(pady=(10, 0))

    lbl_text = tk.Label(
        frame,
        text=caption_text,
        bg='#ff9f9f',
        fg='#6e0c36',
        font=("Helvetica", 12, "bold")
    )
    lbl_text.pack(pady=(5, 0))

    btn = tk.Button(
        frame,
        text=button_text,
        command=root.destroy,
        bg='white',
        fg='black',
        font=("Helvetica", 9, "bold"),
        cursor="hand2"
    )
    btn.pack(pady=10)

    root.mainloop()


def show_picture_popup(image_path: str = "shrimp_snap.jpg"):
    if not os.path.isabs(image_path):
        # Check current working directory or temp path
        if not os.path.exists(image_path):
            base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__)))
            image_path = os.path.join(base_dir, image_path)

    if not os.path.exists(image_path):
        show_basic_popup()
        return

    root = tk.Tk()
    root.attributes('-topmost', True)
    root.overrideredirect(True)

    with Image.open(image_path) as temp_img:
        img = temp_img.copy()

    img.thumbnail((640, 480))
    width, height = img.size

    # Immediately delete snapshot file for privacy
    try:
        os.remove(image_path)
    except Exception:
        pass

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    window_width = width + 20
    window_height = height + 70

    max_x = screen_width - window_width - 50
    max_y = screen_height - window_height - 50
    x = random.randint(50, max_x) if max_x >= 50 else 50
    y = random.randint(50, max_y) if max_y >= 50 else 50

    root.geometry(f"{window_width}x{window_height}+{x}+{y}")

    frame = tk.Frame(root, highlightbackground="#6e0c36", highlightthickness=4, bg='#ff9f9f')
    frame.pack(expand=True, fill='both')

    photo = ImageTk.PhotoImage(img)
    lbl_img = tk.Label(frame, image=photo, bg='#ff9f9f')
    lbl_img.image = photo
    lbl_img.pack(pady=(10, 0))

    btn = tk.Button(
        frame,
        text="I have been exposed...",
        command=root.destroy,
        bg='white',
        fg='black',
        font=("Helvetica", 9, "bold"),
        cursor="hand2"
    )
    btn.pack(pady=10)

    root.mainloop()


def dispatch_popup(popup_type: str, *args):
    """Route popup request based on popup type."""
    if popup_type == 'image1' or popup_type == 'whale':
        show_image_popup("assets/images/whale.jpg", "You're shrimping!", "I will fix my posture!")
    elif popup_type == 'image2' or popup_type == 'krill':
        show_image_popup("assets/images/krill.jpg", "You're slouching!", "My bad!")
    elif popup_type == 'picture':
        snap_path = args[0] if args else "shrimp_snap.jpg"
        show_picture_popup(snap_path)
    else:
        show_basic_popup()


if __name__ == '__main__':
    p_type = sys.argv[1] if len(sys.argv) > 1 else 'basic'
    p_args = sys.argv[2:] if len(sys.argv) > 2 else []
    dispatch_popup(p_type, *p_args)
