# src/scheduler.py
import random
import math
from tkinter import messagebox
from .utils import DAYS, LECTURE_SLOTS, TUTORIAL_SLOTS, LAB_SLOTS

# --- helpers to work with time intervals ---
def _parse_slot_to_minutes(slot):
    """
    slot: "HH:MM-HH:MM" -> (start_minutes, end_minutes)
    """
    start, end = slot.split("-")
    sh, sm = map(int, start.split(":"))
    eh, em = map(int, end.split(":"))
    return sh * 60 + sm, eh * 60 + em

def _intervals_overlap(a_start, a_end, b_start, b_end):
    """
    True if intervals [a_start,a_end) and [b_start,b_end) overlap
    """
    return not (a_end <= b_start or b_end <= a_start)

class TimetableScheduler:
    """
    Scheduler that:
      - uses typed slot pools (lecture/tutorial/lab),
      - enforces no room overlap (checked by real intervals),
      - enforces no student overlap for same branch+semester (real intervals),
      - converts hours-per-week into number-of-slots using per-type slot durations.
    """

    # durations in hours for each type of slot
    TYPE_DURATION = {
        "Lecture": 1.5,
        "Tutorial": 1.0,
        "Lab": 2.0
    }

    TYPE_POOLS = {
        "Lecture": LECTURE_SLOTS,
        "Tutorial": TUTORIAL_SLOTS,
        "Lab": LAB_SLOTS
    }

    def __init__(self, courses=None):
        # courses[branch][sem][code] = {
        #   name, faculty, room, lecture_hours, tutorial_hours, lab_hours
        # }
        self.courses = courses or {}
        # timetable[branch][sem] -> {(day,slot): (code, name, faculty, type, room)}
        self.timetable = {}
        # occupied_rooms: (room, day) -> list of (start_min, end_min)
        self.occupied_rooms = {}
        # branch_sem_intervals: (branch, sem, day) -> list of (start_min, end_min)
        # prevents same students getting overlapping sessions
        self.branch_sem_intervals = {}
        # list of (branch, sem, course_name, type) that couldn't be fully scheduled
        self.unscheduled = []

    def add_course(self, branch, sem, code, name, faculty, room,
                   lecture_hours, tutorial_hours, lab_hours):
        branch, sem = str(branch), str(sem)
        if branch not in self.courses:
            self.courses[branch] = {}
        if sem not in self.courses[branch]:
            self.courses[branch][sem] = {}
        self.courses[branch][sem][code] = {
            "name": name,
            "faculty": faculty,
            "room": room,
            "lecture_hours": int(lecture_hours),
            "tutorial_hours": int(tutorial_hours),
            "lab_hours": int(lab_hours)
        }

    # --- room overlap helpers ---
    def _room_conflicts(self, room, day, slot):
        s_min, e_min = _parse_slot_to_minutes(slot)
        key = (room, day)
        if key not in self.occupied_rooms:
            return False
        for (os, oe) in self.occupied_rooms[key]:
            if _intervals_overlap(s_min, e_min, os, oe):
                return True
        return False

    def _mark_room(self, room, day, slot):
        s_min, e_min = _parse_slot_to_minutes(slot)
        key = (room, day)
        self.occupied_rooms.setdefault(key, []).append((s_min, e_min))

    # --- branch+sem student overlap helpers ---
    def _branch_sem_conflicts(self, branch, sem, day, slot):
        s_min, e_min = _parse_slot_to_minutes(slot)
        key = (branch, sem, day)
        if key not in self.branch_sem_intervals:
            return False
        for (bs, be) in self.branch_sem_intervals[key]:
            if _intervals_overlap(s_min, e_min, bs, be):
                return True
        return False

    def _mark_branch_sem(self, branch, sem, day, slot):
        s_min, e_min = _parse_slot_to_minutes(slot)
        key = (branch, sem, day)
        self.branch_sem_intervals.setdefault(key, []).append((s_min, e_min))

    def generate_timetable(self, notify=True):
        """
        Returns (timetable, unscheduled).
        If notify is True, messageboxes will be shown (UI). Tests should pass notify=False.
        """
        self.timetable.clear()
        self.occupied_rooms.clear()
        self.branch_sem_intervals.clear()
        self.unscheduled.clear()

        for branch, sems in self.courses.items():
            branch = str(branch)
            for sem, courses in sems.items():
                sem = str(sem)
                timetable_branch_sem = {}
                # used_today prevents same course twice in a day (for student convenience)
                used_today = {d: set() for d in DAYS}

                # Make fresh slot pools for this branch+sem (we'll remove assigned slots)
                slot_pools = {
                    ctype: [(d, s) for d in DAYS for s in pool]
                    for ctype, pool in TimetableScheduler.TYPE_POOLS.items()
                }
                # shuffle each pool
                for pool in slot_pools.values():
                    random.shuffle(pool)

                # Go over courses
                for code, info in courses.items():
                    # for each type compute required #slots = ceil(hours / type_duration)
                    type_needs = {
                        "Lecture": max(0, math.ceil(info.get("lecture_hours", 0) / self.TYPE_DURATION["Lecture"])),
                        "Tutorial": max(0, math.ceil(info.get("tutorial_hours", 0) / self.TYPE_DURATION["Tutorial"])),
                        "Lab": max(0, math.ceil(info.get("lab_hours", 0) / self.TYPE_DURATION["Lab"]))
                    }

                    # assign for each type separately
                    for ctype, need in type_needs.items():
                        if need <= 0:
                            continue

                        pool = slot_pools[ctype]
                        count = 0
                        # We'll attempt up to `max_attempts` picks per required session
                        max_attempts = 300

                        while count < need and pool:
                            assigned = False
                            # try several random picks (bounded)
                            for _ in range(max_attempts):
                                if not pool:
                                    break
                                day, slot = random.choice(pool)
                                room = info["room"]

                                # 1) same course not twice in same day
                                if code in used_today[day]:
                                    continue
                                # 2) room conflict (check real overlap)
                                if self._room_conflicts(room, day, slot):
                                    continue
                                # 3) student conflict for this branch+sem (check real overlap)
                                if self._branch_sem_conflicts(branch, sem, day, slot):
                                    continue

                                # All clear → assign
                                timetable_branch_sem[(day, slot)] = (
                                    code, info["name"], info["faculty"], ctype, room
                                )
                                used_today[day].add(code)
                                self._mark_room(room, day, slot)
                                self._mark_branch_sem(branch, sem, day, slot)

                                # remove this specific (day,slot) from pool so we don't reuse it for same sem/type
                                try:
                                    pool.remove((day, slot))
                                except ValueError:
                                    pass

                                count += 1
                                assigned = True
                                break

                            # if we couldn't place any session for this required slot -> break so we avoid infinite loop
                            if not assigned:
                                break

                        # if we failed to place all needed slots, record unscheduled
                        if count < need:
                            self.unscheduled.append((branch, sem, info["name"], ctype))

                # save timetable for branch/sem
                self.timetable.setdefault(branch, {})[sem] = timetable_branch_sem

        # notifications
        if notify:
            if self.unscheduled:
                warn_list = "\n".join([f"{b} Sem-{s}: {c} ({t})" for b, s, c, t in self.unscheduled])
                messagebox.showwarning("Unscheduled Courses",
                                       f"⚠ Some sessions couldn’t be scheduled:\n\n{warn_list}")
            else:
                messagebox.showinfo("Done", "✅ All timetables generated (no student or room overlaps)!")

        return self.timetable, self.unscheduled
