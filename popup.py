import tkinter as tk
import random
import sys

def close_popup():
    root.destroy()

root = tk.Tk()
# Keep it aggressively on top of all other windows
root.attributes('-topmost', True)
# Remove the standard Windows borders to make it look intrusive
root.overrideredirect(True) 

# Grab your screen dimensions
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Pick a completely random coordinate on the screen
x = random.randint(50, screen_width - 350)
y = random.randint(50, screen_height - 250)

# Set the size (300x150) and the random position
root.geometry(f"300x150+{x}+{y}")

# Create a jarring, bright red background frame
frame = tk.Frame(root, highlightbackground="black", highlightthickness=4, bg='#ff4757')
frame.pack(expand=True, fill='both')

# Add the comedic text
lbl = tk.Label(frame, text="🦐 ALERT! 🦐\n\nSHRIMP POSTURE DETECTED!\nUn-shrimp yourself immediately!",
               bg='#ff4757', fg='white', font=("Helvetica", 11, "bold"))
lbl.pack(expand=True, fill='both', pady=(15, 0))

# Add a button so you can physically dismiss it
btn = tk.Button(frame, text="I'm sorry, I'll sit up!", command=close_popup, 
                bg='white', fg='black', font=("Helvetica", 9, "bold"), cursor="hand2")
btn.pack(pady=15)

# Self-destruct the popup after 4 seconds so it doesn't stay forever
root.after(4000, close_popup)

root.mainloop()