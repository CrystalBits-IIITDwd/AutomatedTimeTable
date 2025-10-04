import random
from tkinter import messagebox
from .utils import DAYS, SLOTS

class TimetableScheduler:
    def __init__(self, courses=None):
        self.courses = courses or {}
        self.timetable = {}
        self.occupied_rooms = {}
        self.unscheduled = []

    def add_course(self, branch, sem, code, name, faculty, room, hours):
        if branch not in self.courses:
            self.courses[branch] = {}
        if sem not in self.courses[branch]:
            self.courses[branch][sem] = {}
        self.courses[branch][sem][code] = [name, faculty, room, hours]

    def generate_timetable(self):
        for branch, sems in self.courses.items():
            for sem, sem_courses in sems.items():
                all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
                random.shuffle(all_slots)

                remaining = {code: data[3] for code, data in sem_courses.items()}
                used_today = {day: set() for day in DAYS}
                timetable_branch_sem = {}

                while any(hrs > 0 for hrs in remaining.values()) and all_slots:
                    for code in list(sem_courses.keys()):
                        if remaining[code] <= 0:
                            continue
                        success = False
                        for _ in range(100):
                            if not all_slots:
                                break
                            day, slot = random.choice(all_slots)
                            room = sem_courses[code][2]

                            # same course cannot appear twice in a day
                            if code in used_today[day]:
                                continue
                            # room already occupied
                            if (day, slot) in self.occupied_rooms and room in self.occupied_rooms[(day, slot)]:
                                continue

                            name, faculty, room, _ = sem_courses[code]
                            timetable_branch_sem[(day, slot)] = (name, faculty, room)
                            remaining[code] -= 1.0
                            used_today[day].add(code)

                            if (day, slot) not in self.occupied_rooms:
                                self.occupied_rooms[(day, slot)] = set()
                            self.occupied_rooms[(day, slot)].add(room)

                            all_slots.remove((day, slot))
                            success = True
                            break
                        if not success:
                            self.unscheduled.append((branch, sem, sem_courses[code][0]))

                if branch not in self.timetable:
                    self.timetable[branch] = {}
                self.timetable[branch][sem] = timetable_branch_sem

        if self.unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c}" for b, s, c in self.unscheduled])
            messagebox.showwarning("Unscheduled Courses",
                                   f"⚠ Some courses couldn’t be fully scheduled:\n\n{warn_list}")
        else:
            messagebox.showinfo("Done", "✅ All timetables generated (no room collisions)!")

        return self.timetable, self.unscheduled
