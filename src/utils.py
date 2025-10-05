# utils.py
import csv

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

# Fixed lecture slots (HH:MM format)
SLOTS = [
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

def export_to_csv(timetable):
    for branch, sems in timetable.items():
        for sem, table in sems.items():
            fname = f"timetable_{branch}_Sem{sem}.csv"
            with open(fname, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Day", "Slot", "Course", "Faculty", "Room"])
                for (day, slot), (course, faculty, room) in table.items():
                    writer.writerow([day, slot, course, faculty, room])
