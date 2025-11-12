# scheduler.py
import random
import math
from tkinter import messagebox
from .utils import DAYS, LECTURE_SLOTS, TUTORIAL_SLOTS, LAB_SLOTS, MINOR_SLOTS, LUNCH_BREAK

class TimetableScheduler:
    """
    Enhanced scheduler with:
    - Proper room type matching (Lab courses → Lab rooms)
    - Room capacity constraints
    - CSE section handling (separate/combined)
    - Elective scheduling (all electives together)
    - Minor scheduling (before/after regular hours)
    - Faculty conflict avoidance
    - Combined CSE courses at same time
    - Proper lab room assignment
    """
    
    TYPE_DURATION = {
        "Lecture": 1.5,
        "Tutorial": 1.0,
        "Lab": 2.0
    }

    TYPE_POOLS = {
        "Lecture": LECTURE_SLOTS,
        "Tutorial": TUTORIAL_SLOTS,
        "Lab": LAB_SLOTS,
        "Minor": MINOR_SLOTS
    }

    def __init__(self, courses=None, classrooms=None):
        self.courses = courses or {}
        self.classrooms = {c['room_no']: c for c in (classrooms or [])}
        self.timetable = {}
        self.occupied_rooms = {}
        self.branch_sem_intervals = {}
        self.faculty_schedule = {}
        self.unscheduled = []
        
        # Group courses by type for special handling
        self.elective_courses = []
        self.minor_courses = []
        self._categorize_courses()

    def _categorize_courses(self):
        """Categorize courses into elective, minor, core for special handling."""
        for branch, sems in self.courses.items():
            for sem, courses in sems.items():
                for code, info in courses.items():
                    if info.get('type') == 'elective':
                        self.elective_courses.append((branch, sem, code, info))
                    elif info.get('type') == 'minor':
                        self.minor_courses.append((branch, sem, code, info))

    def _get_room_candidates(self, course_type, required_capacity, room_type=None):
        """Find suitable rooms based on type and capacity."""
        candidates = []
        for room_no, room_info in self.classrooms.items():
            # Check capacity
            if room_info['capacity'] < required_capacity:
                continue
            
            # Enhanced room type matching
            if course_type == "Lab":
                # For labs, prefer actual lab rooms but allow classrooms as fallback
                if room_type == "Lab" and "Lab" not in room_info['type']:
                    continue
                elif room_type == "Classroom" and "Classroom" not in room_info['type']:
                    continue
            elif course_type in ["Lecture", "Tutorial"]:
                # For lectures/tutorials, prefer classrooms but allow labs as fallback
                if room_type == "Classroom" and "Classroom" not in room_info['type']:
                    continue
                elif room_type == "Lab" and "Lab" not in room_info['type']:
                    continue
            
            candidates.append(room_no)
        
        # Sort by capacity (smallest first to optimize room usage)
        candidates.sort(key=lambda r: self.classrooms[r]['capacity'])
        return candidates

    def _parse_slot_to_minutes(self, slot):
        """Convert time slot to minutes for overlap checking."""
        start, end = slot.split("-")
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        return sh * 60 + sm, eh * 60 + em

    def _intervals_overlap(self, a_start, a_end, b_start, b_end):
        """Check if two time intervals overlap."""
        return not (a_end <= b_start or b_end <= a_start)

    def _room_conflicts(self, room, day, slot):
        """Check if room is occupied at given day/slot."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (room, day)
        if key not in self.occupied_rooms:
            return False
        for (os, oe) in self.occupied_rooms[key]:
            if self._intervals_overlap(s_min, e_min, os, oe):
                return True
        return False

    def _mark_room(self, room, day, slot):
        """Mark room as occupied."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (room, day)
        self.occupied_rooms.setdefault(key, []).append((s_min, e_min))

    def _branch_sem_conflicts(self, branch, sem, day, slot):
        """Check if branch-semester has conflict."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (branch, sem, day)
        if key not in self.branch_sem_intervals:
            return False
        for (bs, be) in self.branch_sem_intervals[key]:
            if self._intervals_overlap(s_min, e_min, bs, be):
                return True
        return False

    def _mark_branch_sem(self, branch, sem, day, slot):
        """Mark branch-semester time as occupied."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (branch, sem, day)
        self.branch_sem_intervals.setdefault(key, []).append((s_min, e_min))

    def _faculty_conflicts(self, faculty, day, slot):
        """Check if faculty is teaching elsewhere."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (faculty, day)
        if key not in self.faculty_schedule:
            return False
        for (fs, fe) in self.faculty_schedule[key]:
            if self._intervals_overlap(s_min, e_min, fs, fe):
                return True
        return False

    def _mark_faculty(self, faculty, day, slot):
        """Mark faculty as busy."""
        s_min, e_min = self._parse_slot_to_minutes(slot)
        key = (faculty, day)
        self.faculty_schedule.setdefault(key, []).append((s_min, e_min))

    def _schedule_combined_courses_first(self):
        """Schedule combined CSE courses first to ensure same timing."""
        combined_courses = []
        
        # Find all combined courses
        for branch, sems in self.courses.items():
            if branch not in ["CSE-A", "CSE-B"]:
                continue
            for sem, courses in sems.items():
                for code, info in courses.items():
                    if info.get('linked_pair'):
                        combined_courses.append((branch, sem, code, info))
        
        # Schedule combined courses first
        for branch, sem, code, info in combined_courses:
            other_branch, other_sem, other_code = info['linked_pair']
            
            # Calculate total students for room capacity
            other_info = self.courses.get(other_branch, {}).get(other_sem, {}).get(other_code, {})
            total_students = info.get('students', 0) + other_info.get('students', 0)
            
            # Schedule different types
            type_needs = {
                "Lecture": max(0, math.ceil(info.get("lecture_hours", 0) / self.TYPE_DURATION["Lecture"])),
                "Tutorial": max(0, math.ceil(info.get("tutorial_hours", 0) / self.TYPE_DURATION["Tutorial"])),
                "Lab": max(0, math.ceil(info.get("lab_hours", 0) / self.TYPE_DURATION["Lab"]))
            }
            
            for ctype, need in type_needs.items():
                if need <= 0:
                    continue
                    
                pool = [(d, s) for d in DAYS for s in self.TYPE_POOLS[ctype]]
                random.shuffle(pool)
                
                count = 0
                while count < need and pool:
                    day, slot = pool.pop()
                    
                    # Get room candidates based on type
                    room_candidates = self._get_room_candidates(
                        ctype, total_students, 
                        "Lab" if ctype == "Lab" else "Lecture"
                    )
                    
                    for room in room_candidates:
                        if (self._room_conflicts(room, day, slot) or
                            self._branch_sem_conflicts(branch, sem, day, slot) or
                            self._branch_sem_conflicts(other_branch, other_sem, day, slot) or
                            self._faculty_conflicts(info['faculty'], day, slot)):
                            continue
                            
                        # Schedule for both sections at same time
                        for section, section_sem in [(branch, sem), (other_branch, other_sem)]:
                            self.timetable.setdefault(section, {}).setdefault(section_sem, {})[(day, slot)] = (
                                code, info['name'], info['faculty'], ctype, room
                            )
                            self._mark_branch_sem(section, section_sem, day, slot)
                        
                        self._mark_room(room, day, slot)
                        self._mark_faculty(info['faculty'], day, slot)
                        count += 1
                        break

    def _schedule_minor_courses(self):
        """Schedule minor courses in special slots (before/after regular hours)."""
        minor_slots = [(d, s) for d in DAYS for s in MINOR_SLOTS]
        random.shuffle(minor_slots)
        
        for branch, sem, code, info in self.minor_courses:
            scheduled = False
            for day, slot in minor_slots[:]:  # Copy for safe removal
                if scheduled:
                    break
                    
                # Find suitable room
                room_candidates = self._get_room_candidates(
                    "Lecture", info.get('students', 0)
                )
                
                for room in room_candidates:
                    if (not self._room_conflicts(room, day, slot) and 
                        not self._faculty_conflicts(info['faculty'], day, slot)):
                        
                        # Schedule the minor course
                        self.timetable.setdefault(branch, {}).setdefault(sem, {})[(day, slot)] = (
                            code, info['name'], info['faculty'], "Minor", room
                        )
                        self._mark_room(room, day, slot)
                        self._mark_faculty(info['faculty'], day, slot)
                        minor_slots.remove((day, slot))
                        scheduled = True
                        break
            
            if not scheduled:
                self.unscheduled.append((branch, sem, info['name'], "Minor"))

    def _schedule_elective_courses(self):
        """Schedule elective courses together for each semester."""
        # Group electives by semester
        elective_groups = {}
        for branch, sem, code, info in self.elective_courses:
            elective_groups.setdefault(sem, []).append((branch, code, info))
        
        for sem, electives in elective_groups.items():
            if not electives:
                continue
                
            # Find common slot for all electives of this semester
            elective_slots = [(d, s) for d in DAYS for s in LECTURE_SLOTS]
            random.shuffle(elective_slots)
            
            slot_found = False
            for day, slot in elective_slots:
                if slot_found:
                    break
                    
                # Check if all electives can be scheduled in this slot
                can_schedule_all = True
                room_assignments = {}
                
                for branch, code, info in electives:
                    room_candidates = self._get_room_candidates(
                        "Lecture", info.get('students', 0)
                    )
                    
                    # Find available room for this elective
                    room_found = False
                    for room in room_candidates:
                        if (not self._room_conflicts(room, day, slot) and 
                            not self._faculty_conflicts(info['faculty'], day, slot) and
                            not self._branch_sem_conflicts(branch, sem, day, slot)):
                            room_assignments[(branch, code)] = room
                            room_found = True
                            break
                    
                    if not room_found:
                        can_schedule_all = False
                        break
                
                if can_schedule_all:
                    # Schedule all electives
                    for (branch, code), room in room_assignments.items():
                        info = self.courses[branch][sem][code]
                        self.timetable.setdefault(branch, {}).setdefault(sem, {})[(day, slot)] = (
                            code, info['name'], info['faculty'], "Elective", room
                        )
                        self._mark_room(room, day, slot)
                        self._mark_faculty(info['faculty'], day, slot)
                        self._mark_branch_sem(branch, sem, day, slot)
                    slot_found = True
            
            if not slot_found:
                for branch, code, info in electives:
                    self.unscheduled.append((branch, sem, info['name'], "Elective"))

    def _schedule_labs_properly(self):
        """Schedule lab courses with proper lab room assignment."""
        lab_courses = []
        
        # Find all lab courses that haven't been scheduled yet
        for branch, sems in self.courses.items():
            for sem, courses in sems.items():
                for code, info in courses.items():
                    if info.get('lab_hours', 0) > 0:
                        # Check if already scheduled
                        already_scheduled = False
                        if branch in self.timetable and sem in self.timetable[branch]:
                            for (day, slot), (scheduled_code, _, _, ctype, _) in self.timetable[branch][sem].items():
                                if scheduled_code == code and ctype == "Lab":
                                    already_scheduled = True
                                    break
                        if not already_scheduled:
                            lab_courses.append((branch, sem, code, info))
        
        # Sort by lab hours (more lab hours first)
        lab_courses.sort(key=lambda x: x[3].get('lab_hours', 0), reverse=True)
        
        for branch, sem, code, info in lab_courses:
            need = max(0, math.ceil(info.get("lab_hours", 0) / self.TYPE_DURATION["Lab"]))
            if need <= 0:
                continue
                
            pool = [(d, s) for d in DAYS for s in LAB_SLOTS]
            random.shuffle(pool)
            
            count = 0
            while count < need and pool:
                day, slot = pool.pop()
                
                # Get lab room candidates - prioritize actual lab rooms
                lab_room_candidates = self._get_room_candidates("Lab", info.get('students', 0), "Lab")
                classroom_candidates = self._get_room_candidates("Lab", info.get('students', 0), "Classroom")
                room_candidates = lab_room_candidates + classroom_candidates  # Prefer labs first
                
                for room in room_candidates:
                    if (self._room_conflicts(room, day, slot) or
                        self._branch_sem_conflicts(branch, sem, day, slot) or
                        self._faculty_conflicts(info['faculty'], day, slot)):
                        continue
                        
                    # Schedule the lab
                    self.timetable.setdefault(branch, {}).setdefault(sem, {})[(day, slot)] = (
                        code, info['name'], info['faculty'], "Lab", room
                    )
                    self._mark_room(room, day, slot)
                    self._mark_branch_sem(branch, sem, day, slot)
                    self._mark_faculty(info['faculty'], day, slot)
                    count += 1
                    break

    def _schedule_regular_courses(self):
        """Schedule regular core courses."""
        for branch, sems in self.courses.items():
            # Skip if already scheduled as elective/minor
            if any((branch, sem, code, info) in self.elective_courses + self.minor_courses 
                   for sem, courses in sems.items() for code, info in courses.items()):
                continue
                
            for sem, courses in sems.items():
                timetable_branch_sem = {}
                used_today = {d: set() for d in DAYS}

                # Create slot pools for this branch-semester
                slot_pools = {
                    ctype: [(d, s) for d in DAYS for s in pool] 
                    for ctype, pool in self.TYPE_POOLS.items() 
                    if ctype != "Minor"  # Minors already scheduled
                }
                for pool in slot_pools.values():
                    random.shuffle(pool)

                for code, info in courses.items():
                    # Skip if already scheduled
                    if (branch, sem, code, info) in self.elective_courses + self.minor_courses:
                        continue

                    type_needs = {
                        "Lecture": max(0, math.ceil(info.get("lecture_hours", 0) / self.TYPE_DURATION["Lecture"])),
                        "Tutorial": max(0, math.ceil(info.get("tutorial_hours", 0) / self.TYPE_DURATION["Tutorial"])),
                        "Lab": max(0, math.ceil(info.get("lab_hours", 0) / self.TYPE_DURATION["Lab"]))
                    }

                    for ctype, need in type_needs.items():
                        if need <= 0:
                            continue

                        pool = slot_pools[ctype]
                        count = 0
                        max_attempts = len(pool) * 2

                        while count < need and pool and max_attempts > 0:
                            max_attempts -= 1
                            day, slot = random.choice(pool)

                            # Determine room type and get candidates
                            room_type = "Lab" if ctype == "Lab" else "Lecture"
                            room_candidates = self._get_room_candidates(
                                room_type, info.get('students', 0)
                            )

                            for room in room_candidates:
                                if (code in used_today[day] or
                                    self._room_conflicts(room, day, slot) or
                                    self._branch_sem_conflicts(branch, sem, day, slot) or
                                    self._faculty_conflicts(info['faculty'], day, slot)):
                                    continue

                                # Schedule the course
                                timetable_branch_sem[(day, slot)] = (
                                    code, info['name'], info['faculty'], ctype, room
                                )
                                used_today[day].add(code)
                                self._mark_room(room, day, slot)
                                self._mark_branch_sem(branch, sem, day, slot)
                                self._mark_faculty(info['faculty'], day, slot)

                                try:
                                    pool.remove((day, slot))
                                except ValueError:
                                    pass

                                count += 1
                                break

                        if count < need:
                            self.unscheduled.append((branch, sem, info['name'], ctype))

                self.timetable.setdefault(branch, {})[sem] = timetable_branch_sem

    def generate_timetable(self, notify=True):
        """Generate complete timetable with all course types."""
        self.timetable.clear()
        self.occupied_rooms.clear()
        self.branch_sem_intervals.clear()
        self.faculty_schedule.clear()
        self.unscheduled.clear()

        # NEW: Schedule in improved priority order
        self._schedule_combined_courses_first()  # Combined CSE courses first
        self._schedule_minor_courses()           # Minors second  
        self._schedule_elective_courses()        # Electives third
        self._schedule_labs_properly()           # Labs fourth (with proper room assignment)
        self._schedule_regular_courses()         # Regular courses last

        if notify:
            self._notify_results()

        return self.timetable, self.unscheduled

    def _notify_results(self):
        """Notify user about scheduling results."""
        total_scheduled = sum(len(sems) for sems in self.timetable.values())
        if self.unscheduled:
            warn_list = "\n".join([f"{b} Sem-{s}: {c} ({t})" for b, s, c, t in self.unscheduled])
            messagebox.showwarning(
                "Partial Completion", 
                f"✅ Scheduled {total_scheduled} timetables\n\n"
                f"⚠ Some sessions couldn't be scheduled:\n\n{warn_list}"
            )
        else:
            branches = list(self.timetable.keys())
            branch_info = ", ".join(branches)
            messagebox.showinfo(
                "Success", 
                f"✅ All timetables generated successfully!\n"
                f"Branches: {branch_info}\n"
                f"Scheduled {total_scheduled} branch-semester combinations."
            )


class ExamScheduler:
    """Automatic exam timetable scheduler."""
    
    def __init__(self, courses=None, classrooms=None):
        self.courses = courses or {}
        self.classrooms = {c['room_no']: c for c in (classrooms or [])}
        self.exam_schedule = []
        self.occupied_rooms = {}
        self.branch_sem_exams = {}
        
        # Exam slots (2-3 hour durations)
        self.exam_slots = [
            "09:00-12:00",
            "14:00-17:00",
            "18:00-21:00"
        ]
    
    def generate_exam_schedule(self):
        """Generate conflict-free exam schedule."""
        self.exam_schedule.clear()
        self.occupied_rooms.clear()
        self.branch_sem_exams.clear()
        
        # Collect all courses that need exams
        exam_courses = []
        for branch, sems in self.courses.items():
            for sem, courses in sems.items():
                for code, info in courses.items():
                    # Skip labs for theory exams, adjust as needed
                    if info.get('lab_hours', 0) > 0 and info.get('lecture_hours', 0) == 0:
                        continue
                    exam_courses.append((branch, sem, code, info))
        
        # Sort by student count (larger exams first)
        exam_courses.sort(key=lambda x: x[3].get('students', 0), reverse=True)
        
        for branch, sem, code, info in exam_courses:
            scheduled = False
            student_count = info.get('students', 0)
            
            # Find suitable rooms
            room_candidates = self._get_room_candidates(student_count)
            if not room_candidates:
                continue
                
            for day in DAYS:
                if scheduled:
                    break
                for slot in self.exam_slots:
                    if scheduled:
                        break
                    
                    # Check branch-semester conflict
                    if self._has_branch_sem_exam(branch, sem, day, slot):
                        continue
                    
                    # Find available room
                    for room in room_candidates:
                        if not self._is_room_occupied(room, day, slot):
                            # Schedule exam
                            self.exam_schedule.append({
                                'day': day,
                                'slot': slot,
                                'code': code,
                                'name': info['name'],
                                'branch': branch,
                                'semester': sem,
                                'room': room
                            })
                            self._mark_room_occupied(room, day, slot)
                            self._mark_branch_sem_exam(branch, sem, day, slot)
                            scheduled = True
                            break
        
        return self.exam_schedule
    
    def _get_room_candidates(self, required_capacity):
        """Find rooms with sufficient capacity."""
        return [room for room, info in self.classrooms.items() 
                if info['capacity'] >= required_capacity]
    
    def _is_room_occupied(self, room, day, slot):
        """Check if room is occupied for exams."""
        return (room, day, slot) in self.occupied_rooms
    
    def _mark_room_occupied(self, room, day, slot):
        """Mark room as occupied for exam."""
        self.occupied_rooms[(room, day, slot)] = True
    
    def _has_branch_sem_exam(self, branch, sem, day, slot):
        """Check if branch-semester already has exam."""
        return (branch, sem, day, slot) in self.branch_sem_exams
    
    def _mark_branch_sem_exam(self, branch, sem, day, slot):
        """Mark branch-semester as having exam."""
        self.branch_sem_exams[(branch, sem, day, slot)] = True