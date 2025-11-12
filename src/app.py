# app.py
import tkinter as tk
from tkinter import ttk
from .ui import TimetableApp

def main():
    root = tk.Tk()
    root.title("🎓 Automated Timetable & Exam Scheduler")
    root.geometry("1450x750")
    
    # Create notebook for tabs
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Create the app with notebook
    app = TimetableApp(notebook)
    
    root.mainloop()

if __name__ == "__main__":
    main()