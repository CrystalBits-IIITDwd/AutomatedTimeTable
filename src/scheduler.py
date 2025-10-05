import random
import math
from tkinter import messagebox
from .utils import DAYS, SLOTS

def _parse_slot_to_minutes(slot):
    """
    slot: "HH:MM-HH:MM" -> (start_minutes, end_minutes)
    """
    start, end = slot.split("-")
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return sh * 60 + sm, eh * 60 + em

def _intervals_overlap(a_start, a_end, b_start, b_end):
    return not (a_end <= b_start or b_end <= a_start)

class TimetableScheduler:
    SLOT_DURATION = 1.5  # hours per slot (matching the fixed slots list)

    def __init__(self, courses=None):
        # courses: dict[branch][sem][code] = [name, faculty, room, hours]
        self.courses = courses or {}
        self.timetable = {}       # branch -> sem -> {(day,slot): (course,faculty,room)}
        # occupied_rooms: key = (room, day) -> list of (start_min, end_min)
        self.occupied_rooms = {}
        self.unscheduled = []

    def add_course(self, branch, sem, code, name, faculty, room, hours):
        branch = str(branch)
        sem = str(sem)
        if branch not in self.courses:
            self.courses[branch] = {}
        if sem not in self.courses[branch]:
            self.courses[branch][sem] = {}
        self.courses[branch][sem][code] = [name, faculty, room, float(hours)]

    def _room_conflicts(self, room, day, slot):
        """Return True if (room,day,slot) conflicts with existing occupied intervals."""
        start_min, end_min = _parse_slot_to_minutes(slot)
        key = (room, day)
        if key not in self.occupied_rooms:
            return False
        for (s, e) in self.occupied_rooms[key]:
            if _intervals_overlap(start_min, end_min, s, e):
                return True
        return False

    def _mark_room_occupied(self, room, day, slot):
        start_min, end_min = _parse_slot_to_minutes(slot)
        key = (room, day)
        if key not in self.occupied_rooms:
            self.occupied_rooms[key] = []
        self.occupied_rooms[key].append((start_min, end_min))

    def generate_timetable(self, notify=True):
        """Generate timetable. If notify False, no messagebox popups (useful for tests)."""
        self.timetable.clear()
        self.occupied_rooms.clear()
        self.unscheduled.clear()

        for branch, sems in self.courses.items():
            branch = str(branch)
            for sem, sem_courses in sems.items():
                sem = str(sem)
                all_slots = [(day, slot) for day in DAYS for slot in SLOTS]
                random.shuffle(all_slots)

                # convert hours -> number of required slots (ceil to ensure coverage)
                remaining = {
                    code: max(1, math.ceil(data[3] / self.SLOT_DURATION))
                    for code, data in sem_courses.items()
                }

                used_today = {day: set() for day in DAYS}
                timetable_branch_sem = {}

                # while there is any course that still needs slots and we still have candidate slots
                while any(hrs > 0 for hrs in remaining.values()) and all_slots:
                    progress_made = False
                    for code in list(sem_courses.keys()):
                        if remaining[code] <= 0:
                            continue

                        success = False
                        # try up to N random slots to place this course
                        for _ in range(100):
                            if not all_slots:
                                break
                            day, slot = random.choice(all_slots)
                            name, faculty, room, _ = sem_courses[code]

                            # avoid same course twice per day
                            if code in used_today[day]:
                                continue

                            # avoid room time overlap (checks real time intervals)
                            if self._room_conflicts(room, day, slot):
                                continue

                            # assign slot
                            timetable_branch_sem[(day, slot)] = (name, faculty, room)
                            remaining[code] -= 1
                            used_today[day].add(code)
                            # mark room occupied for that day/time interval
                            self._mark_room_occupied(room, day, slot)

                            # don't reuse the same (day,slot) for this sem again
                            try:
                                all_slots.remove((day, slot))
                            except ValueError:
                                pass

                            success = True
                            progress_made = True
                            break

                        if not success and remaining[code] > 0:
                            # only append once
                            entry = (branch, sem, sem_courses[code][0])
                            if entry not in self.unscheduled:
                                self.unscheduled.append(entry)

                    # if we couldn't place any course in a full iteration -> break to avoid infinite loop
                    if not progress_made:
                        break

                if branch not in self.timetable:
                    self.timetable[branch] = {}
                self.timetable[branch][sem] = timetable_branch_sem

        if self.unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c}" for b, s, c in self.unscheduled])
            if notify:
                messagebox.showwarning(
                    "Unscheduled Courses",
                    f"⚠ Some courses couldn’t be fully scheduled:\n\n{warn_list}"
                )
        else:
            if notify:
                messagebox.showinfo("Done", "✅ All timetables generated (hours per week honored, no room collisions)!")

        return self.timetable, self.unscheduled
