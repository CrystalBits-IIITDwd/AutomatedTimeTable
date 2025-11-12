# utils.py
import csv

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Regular class slots (9:00-17:10)
LECTURE_SLOTS = [
    "09:00-10:30",
    "10:45-12:15",
    "14:30-16:00",  # After lunch break
    "16:15-17:45"
]

TUTORIAL_SLOTS = [
    "12:15-13:15",
    "17:45-18:45"
]

LAB_SLOTS = [
    "09:00-11:00",
    "11:15-13:15",
    "14:30-16:30",
    "16:45-18:45"
]

# Special slots for minors (before/after regular hours)
MINOR_SLOTS = [
    "07:30-09:00",  # Before regular classes
    "18:00-19:30"   # After regular classes
]

LUNCH_BREAK = ("13:15", "14:30")  # Lunch time range

SLOTS = LECTURE_SLOTS + TUTORIAL_SLOTS + LAB_SLOTS

def export_to_csv(timetable, filename_prefix="timetable"):
    """Exports the given timetable dictionary into CSV files per branch and semester."""
    for branch, sems in timetable.items():
        for sem, table in sems.items():
            fname = f"{filename_prefix}_{branch}_Sem{sem}.csv"
            with open(fname, "w", newline="", encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Day", "Time Slot", "Course Code", "Course Name", "Faculty", "Type", "Room"])
                for (day, slot), (code, name, faculty, ctype, room) in sorted(table.items()):
                    writer.writerow([day, slot, code, name, faculty, ctype, room])
    return f"Exported {sum(len(sems) for sems in timetable.values())} timetable files"

def export_exam_schedule(exam_schedule, filename="exam_schedule.csv"):
    """Exports exam schedule to CSV."""
    with open(filename, "w", newline="", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Day", "Time Slot", "Course Code", "Course Name", "Branch", "Semester", "Room"])
        for entry in exam_schedule:
            writer.writerow([
                entry['day'], entry['slot'], entry['code'], 
                entry['name'], entry['branch'], entry['semester'], entry['room']
            ])
    return f"Exported exam schedule with {len(exam_schedule)} entries"