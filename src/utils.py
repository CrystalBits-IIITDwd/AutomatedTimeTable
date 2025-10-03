import csv
from datetime import datetime, timedelta

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri"]

def generate_slots():
    start = datetime.strptime("09:00", "%H:%M")
    end = datetime.strptime("17:00", "%H:%M")
    slots = []
    lunch_start = datetime.strptime("13:15", "%H:%M")
    lunch_end = datetime.strptime("14:30", "%H:%M")

    while start < end:
        one_hour = start + timedelta(hours=1)
        ninety_min = start + timedelta(minutes=90)

        if not (start < lunch_end and one_hour > lunch_start):
            slots.append((start.strftime("%H:%M"), one_hour.strftime("%H:%M")))
        if not (start < lunch_end and ninety_min > lunch_start):
            slots.append((start.strftime("%H:%M"), ninety_min.strftime("%H:%M")))

        start += timedelta(minutes=30)

    return [f"{s}-{e}" for s, e in slots]

SLOTS = generate_slots()

def export_to_csv(timetable):
    for branch, sems in timetable.items():
        for sem, table in sems.items():
            fname = f"timetable_{branch}_Sem{sem}.csv"
            with open(fname, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Day", "Slot", "Course", "Faculty", "Room"])
                for (day, slot), (course, faculty, room) in table.items():
                    writer.writerow([day, slot, course, faculty, room])
