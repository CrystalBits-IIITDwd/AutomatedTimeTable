# utils.py
import csv

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Slots categorized by type
LECTURE_SLOTS = [
    "09:00-10:30",
    "10:45-12:15",
    "14:00-15:30",
    "15:40-17:10",
    "17:10-18:30",
    "16:00-17:30",
    "10:30-12:00",
    "11:00-12:30",
    "10:00-11:30",
    "11:30-13:00",
]

TUTORIAL_SLOTS = [
    "12:15-13:15",
    "17:30-18:30"
]

LAB_SLOTS = [
    "09:00-11:00",
    "11:00-13:00",
    "14:00-16:00"
]

# Combined list expected by tests / utilities
SLOTS = LECTURE_SLOTS + TUTORIAL_SLOTS + LAB_SLOTS

def export_to_csv(timetable):
    for branch, sems in timetable.items():
        for sem, table in sems.items():
            fname = f"timetable_{branch}_Sem{sem}.csv"
            with open(fname, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Day", "Slot", "Course Code", "Course Name", "Faculty", "Type", "Room"])
                for (day, slot), (code, name, faculty, ctype, room) in table.items():
<<<<<<< HEAD
                    writer.writerow([day, slot, code, name, faculty, ctype, room])
=======
                    writer.writerow([day, slot, code, name, faculty, ctype, room])
>>>>>>> 048547a4d3fbd5b246f21809d2531d1547ef4e09