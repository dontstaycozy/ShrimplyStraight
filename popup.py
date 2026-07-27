import tkinter as tk
import random
import sys

def close_popup():
    root.destroy()

root = tk.Tk()
root.attributes('-topmost', True)
root.overrideredirect(True) 

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = random.randint(50, screen_width - 350)
y = random.randint(50, screen_height - 250)

root.geometry(f"300x150+{x}+{y}")

frame = tk.Frame(root, highlightbackground="#6e0c36", highlightthickness=4, bg='#ff9f9f')
frame.pack(expand=True, fill='both')

lbl = tk.Label(frame, text="🦐 ALERT! 🦐\n\nShrimp DETECTED!\nUn-shrimp yourself immediately!",
               bg='#ff9f9f', fg='#6e0c36', font=("Helvetica", 11, "bold"))
lbl.pack(expand=True, fill='both', pady=(15, 0))

btn = tk.Button(frame, text="I'm sorry, I'll sit up!", command=close_popup,     
                bg='white', fg='black', font=("Helvetica", 9, "bold"), cursor="hand2")
btn.pack(pady=15)

root.mainloop()