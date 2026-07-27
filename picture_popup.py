import tkinter as tk
from PIL import Image, ImageTk
import random
import os
import sys

def close_popup():
    root.destroy()

root = tk.Tk()
root.attributes('-topmost', True)
root.overrideredirect(True) 

image_path = "shrimp_snap.jpg"
if os.path.exists(image_path):
    with Image.open(image_path) as temp_img:
        img = temp_img.copy()
    
    img.thumbnail((640, 480))
    width, height = img.size
    
    try:
        os.remove(image_path)
    except Exception:
        pass
else:
    root.destroy()
    sys.exit()

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

btn = tk.Button(frame, text="I have been exposed...", command=close_popup,     
                bg='white', fg='black', font=("Helvetica", 9, "bold"), cursor="hand2")
btn.pack(pady=10)

root.mainloop()
