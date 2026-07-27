import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import random
import os
import sys

def close_popup():
    root.destroy()

root = tk.Tk()
root.attributes('-topmost', True)
root.overrideredirect(True) 

image_path = "krill.jpg"

if os.path.exists(image_path):
    img = Image.open(image_path)
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

lbl_text = tk.Label(frame, text="You're slouching! (Replace placeholder2.png)",
               bg='#ff9f9f', fg='#6e0c36', font=("Helvetica", 10, "bold"))
lbl_text.pack(pady=(5, 0))

btn = tk.Button(frame, text="My bad!", command=close_popup,     
                bg='white', fg='black', font=("Helvetica", 9, "bold"), cursor="hand2")
btn.pack(pady=10)

root.mainloop()
