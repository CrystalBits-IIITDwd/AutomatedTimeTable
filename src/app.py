import tkinter as tk
from .ui import TimetableApp

def main():
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()
