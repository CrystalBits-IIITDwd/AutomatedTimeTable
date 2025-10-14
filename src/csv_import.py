import csv
from tkinter import messagebox

def load_classrooms(csv_path):
    """Reads classroom CSV and returns a list of dicts."""
    classrooms = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_cols = {"room no", "room type", "room capacity"}
            if not required_cols.issubset({c.strip().lower() for c in reader.fieldnames}):
                messagebox.showerror("Error", "Invalid Classroom CSV format!")
                return []
            for row in reader:
                classrooms.append({
                    "room_no": row.get("room no", "").strip(),
                    "room_type": row.get("room type", "").strip().lower(),
                    "capacity": int(row.get("room capacity", 0)),
                })
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read classrooms CSV: {e}")
    return classrooms


def load_courses(csv_path):
    """Reads course CSV and returns a list of dicts."""
    courses = []
    try:
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            required_cols = {
                "course code", "course name", "faculty name",
                "l-t-p-s-c", "no. of students registered",
                "semester", "branch"
            }
            if not required_cols.issubset({c.strip().lower() for c in reader.fieldnames}):
                messagebox.showerror("Error", "Invalid Course CSV format!")
                return []
            for row in reader:
                ltp = row.get("l-t-p-s-c", "0-0-0-0-0").split("-")
                ltp = [int(x) if x.isdigit() else 0 for x in ltp]
                faculty = [f.strip() for f in row.get("faculty name", "").split(",")]
                courses.append({
                    "code": row.get("course code", "").strip(),
                    "name": row.get("course name", "").strip(),
                    "faculty": faculty,
                    "lecture_hours": ltp[0],
                    "tutorial_hours": ltp[1],
                    "lab_hours": ltp[2],
                    "students": int(row.get("no. of students registered", 0)),
                    "semester": row.get("semester", "").strip(),
                    "branch": row.get("branch", "").strip().upper()
                })
    except Exception as e:
        messagebox.showerror("Error", f"Failed to read courses CSV: {e}")
    return courses
