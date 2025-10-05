import random
from tkinter import messagebox
from .utils import DAYS, SLOTS

class TimetableScheduler:
    SLOT_DURATION = 1.5  # hours per slot (e.g. 9–10:30, 10:45–12:15, etc.)

    def __init__(self, courses=None):
        self.courses = courses or {}
        self.timetable = {}       # branch -> sem -> (day, slot) -> (course, faculty, room)
        self.occupied_rooms = {}  # (day, slot) -> set(rooms)
        self.unscheduled = []

    def add_course(self, branch, sem, code, name, faculty, room, hours):
        branch = str(branch)
        sem = str(sem)
        if branch not in self.courses:
            self.courses[branch] = {}
        if sem not in self.courses[branch]:
            self.courses[branch][sem] = {}
        self.courses[branch][sem][code] = [name, faculty, room, float(hours)]

    def generate_timetable(self):
        self.timetable.clear()
        self.occupied_rooms.clear()
        self.unscheduled.clear()

        for branch, sems in self.courses.items():
            branch = str(branch)
            for sem, sem_courses in sems.items():
                sem = str(sem)
                all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
                random.shuffle(all_slots)

                # convert hours → number of required slots
                remaining = {
                    code: max(1, int(round(data[3] / self.SLOT_DURATION)))
                    for code, data in sem_courses.items()
                }

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
                            name, faculty, room, _ = sem_courses[code]

                            # avoid same course twice per day
                            if code in used_today[day]:
                                continue
                            # avoid room conflicts
                            if (day, slot) in self.occupied_rooms and room in self.occupied_rooms[(day, slot)]:
                                continue

                            # assign slot
                            timetable_branch_sem[(day, slot)] = (name, faculty, room)
                            remaining[code] -= 1
                            used_today[day].add(code)

                            if (day, slot) not in self.occupied_rooms:
                                self.occupied_rooms[(day, slot)] = set()
                            self.occupied_rooms[(day, slot)].add(room)

                            all_slots.remove((day, slot))
                            success = True
                            break

                        if not success and remaining[code] > 0:
                            if (branch, sem, sem_courses[code][0]) not in self.unscheduled:
                                self.unscheduled.append((branch, sem, sem_courses[code][0]))

                if branch not in self.timetable:
                    self.timetable[branch] = {}
                self.timetable[branch][sem] = timetable_branch_sem

        if self.unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c}" for b, s, c in self.unscheduled])
            messagebox.showwarning(
                "Unscheduled Courses",
                f"⚠ Some courses couldn’t be fully scheduled:\n\n{warn_list}"
            )
        else:
            messagebox.showinfo("Done", "✅ All timetables generated (hours per week honored, no room collisions)!")

        return self.timetable, self.unscheduled
