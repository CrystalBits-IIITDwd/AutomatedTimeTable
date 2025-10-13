🎓 Automated Timetable Generator – IIIT Dharwad

Team Crystal Bits | Version 1.0

🧩 Overview

The Automated Timetable Generator is a Python-based desktop application designed to automatically generate conflict-free academic timetables for IIIT Dharwad.

It efficiently assigns courses, faculty, and rooms across lecture, tutorial, and lab sessions — ensuring there are no room overlaps or student schedule conflicts.

This is the first version (v1.0) of the software developed by Team Crystal Bits, and future updates will include:

Importing course data from CSV or Excel files

Advanced scheduling preferences (faculty or time-based)

Cloud data storage and sharing

Automated conflict resolution and optimization

👥 Team Crystal Bits
Member Name	Role
Sugyan Singh	Backend & Logic Design
Nitish Kumar	UI Development & Integration
Nikhil Sinha	Data Models & Utilities
Naveena Shree	Scheduler & QA Testing
🏗️ Project Structure
Automated Timetable/
│
├── src/
│   ├── __init__.py
│   ├── app.py
│   ├── models.py
│   ├── scheduler.py
│   ├── ui.py
│   └── utils.py
│
└── README.md

🧠 File Descriptions
app.py

The main entry point of the application.
It initializes the Tkinter root window and launches the GUI by instantiating TimetableApp from ui.py.

import tkinter as tk
from .ui import TimetableApp

def main():
    root = tk.Tk()
    app = TimetableApp(root)
    root.mainloop()

models.py

Defines the Course model that stores and manages course information.
It supports both simple and detailed forms of course definitions (lecture/tutorial/lab hours, branch, semester, etc.).

Key Responsibilities:

Represents course data in a structured form

Provides compatibility with older input formats

Handles dynamic attributes like lecture, tutorial, and lab rooms

scheduler.py

Implements the TimetableScheduler, which is the heart of the project.
It ensures that:

No room overlaps occur

No student conflicts occur (same branch + semester)

Course hours are distributed across available slots

Proper distinction between lecture, tutorial, and lab sessions

Core Features:

Uses slot pools categorized by session type

Randomized slot assignment to maximize coverage

Reports unscheduled sessions if conflicts prevent placement

ui.py

Builds the Graphical User Interface (GUI) using Tkinter.
Users can:

Add, edit, or remove courses

Generate timetables automatically

View and export generated timetables to CSV

Sections of the UI:

Course entry form

Timetable viewer

Course edit/remove panel

Export options

Tech Used: Tkinter, ttk, messagebox

utils.py

Contains helper functions and constants used throughout the project.

Includes:

Defined constants for days and time slots

CSV export functionality for saving generated timetables

Slot duration mapping for lectures, tutorials, and labs

⚙️ Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/<your-username>/Automated-Timetable.git
cd Automated-Timetable/src

2️⃣ Install Dependencies

The app requires only standard Python libraries (Tkinter, CSV, Math, Random).

If you’re on Linux and Tkinter isn’t installed:

sudo apt-get install python3-tk

3️⃣ Run the Application
python -m src.app


or

python src/app.py

🖥️ Usage Instructions

Launch the Application

Run python app.py or python -m src.app

Add Courses

Enter details such as Course Code, Name, Faculty, Rooms, and Hours

Select Branch and Semester, then click “➕ Add Course”

Generate Timetable

Click “⚡ Generate All” to automatically create a conflict-free timetable

View Timetable

Use “📖 Show Timetable” to view the schedule for a specific branch and semester

Export Timetable

Use “📤 Export CSV” to save the timetable data for sharing or backup

🧾 Example Output

Timetable View Example (CSE, Sem 3)

Day	Slot	Course Code	Course Name	Faculty	Type	Room
Mon	09:00-10:30	CS201	Data Structures	Prof. X	Lecture	CR-01
Mon	14:00-15:30	CS202	Discrete Math	Prof. Y	Tutorial	CR-02
Tue	10:45-12:15	CS201	Data Structures	Prof. X	Lecture	CR-01
🚀 Future Enhancements

Faculty-wise timetable export

Lab scheduling optimization

Integration with Google Calendar / ICS

Faculty availability constraints

Multi-campus support

📜 License

This project is licensed under the MIT License.
You are free to use, modify, and distribute the software with proper attribution.