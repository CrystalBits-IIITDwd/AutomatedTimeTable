import random
from tkinter import messagebox
from .utils import DAYS, SLOTS

def TimetableScheduler(courses):
    timetable = {}
    occupied_rooms = {}
    unscheduled = []

    for branch, sems in courses.items():
        for sem, courses in sems.items():
            all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
            random.shuffle(all_slots)
            remaining = {code: data[3] for code, data in courses.items()}
            used_today = {day: set() for day in DAYS}
            timetable_branch_sem = {}

            while any(hrs > 0 for hrs in remaining.values()) and all_slots:
                for code in list(courses.keys()):
                    if remaining[code] <= 0:
                        continue
                    success = False
                    for _ in range(100):  # retry attempts
                        if not all_slots:
                            break
                        day, slot = random.choice(all_slots)
                        room = courses[code][2]

                        # no same course twice in same day
                        if code in used_today[day]:
                            continue
                        # room already occupied
                        if (day, slot) in occupied_rooms and room in occupied_rooms[(day, slot)]:
                            continue

                        name, faculty, room, _ = courses[code]
                        timetable_branch_sem[(day, slot)] = (name, faculty, room)
                        remaining[code] -= 1.0
                        used_today[day].add(code)

                        if (day, slot) not in occupied_rooms:
                            occupied_rooms[(day, slot)] = set()
                        occupied_rooms[(day, slot)].add(room)

                        all_slots.remove((day, slot))
                        success = True
                        break
                    if not success:
                        unscheduled.append((branch, sem, courses[code][0]))

            if branch not in timetable:
                timetable[branch] = {}
            timetable[branch][sem] = timetable_branch_sem

    if unscheduled:
        warn_list = "\n".join([f"{b} Sem-{s}: {c}" for b, s, c in unscheduled])
        messagebox.showwarning("Unscheduled Courses",
                               f"⚠ Some courses couldn’t be fully scheduled:\n\n{warn_list}")
    else:
        messagebox.showinfo("Done", "✅ All timetables generated (no room collisions)!")

    return timetable
