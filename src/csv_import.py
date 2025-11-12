# csv_import.py
import csv
from tkinter import messagebox
import os
import re

def _pick_column(fieldnames, variants):
    """Return the first matching column from variants (case-insensitive)."""
    if not fieldnames:
        return None
    low = {f.strip().lower(): f for f in fieldnames}
    for v in variants:
        if v.lower() in low:
            return low[v.lower()]
    return None

def _safe_int(value, default=0):
    """Try to convert to int, fallback gracefully."""
    try:
        return int(float(str(value).strip()))
    except Exception:
        return default

def load_classrooms(csv_path):
    """
    Reads classrooms CSV with format: Room no, Capacity, Type
    """
    classrooms = []

    if not os.path.exists(csv_path):
        messagebox.showerror("Error", f"File not found: {csv_path}")
        return []

    try:
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = ',' if ',' in sample else '\t'
            
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                messagebox.showerror("Error", "Empty or invalid CSV file for classrooms.")
                return []

            # Normalize column names
            fieldnames = [f.strip().lower() for f in reader.fieldnames]
            reader.fieldnames = fieldnames
            
            room_col = _pick_column(fieldnames, ["room no", "room_no", "room id", "room"])
            cap_col = _pick_column(fieldnames, ["capacity", "cap"])
            type_col = _pick_column(fieldnames, ["type", "room type"])

            if not all([room_col, cap_col, type_col]):
                messagebox.showerror("Error", "Classrooms CSV must contain: Room no, Capacity, Type")
                return []

            for row in reader:
                classroom = {
                    "room_no": str(row[room_col]).strip(),
                    "capacity": _safe_int(row[cap_col]),
                    "type": str(row[type_col]).strip(),
                    "facilities": ""  # Optional field
                }
                classrooms.append(classroom)

        messagebox.showinfo("Success", f"Loaded {len(classrooms)} classrooms")
        return classrooms

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read classrooms CSV:\n{e}")
        return []

def parse_ltpsc(ltpsc_str):
    """Parse L-T-P-S-C format and return lecture, tutorial, lab hours."""
    try:
        # Handle formats like "3-1-0-0-4" or "3-1-2"
        parts = [p.strip() for p in str(ltpsc_str).split("-")]
        if len(parts) >= 3:
            return _safe_int(parts[0]), _safe_int(parts[1]), _safe_int(parts[2])
        else:
            return 0, 0, 0
    except Exception:
        return 0, 0, 0

def parse_branch_semester(branch_str, sem_str):
    """Parse branch and semester information with special handling."""
    branch = str(branch_str).strip().upper()
    sem = str(sem_str).strip()
    
    # Handle "all" branch and multiple semesters
    if branch in ["ALL", "COMMON"]:
        branch = "ALL"
    
    # Handle multiple semesters like "3 & 5"
    if "&" in sem:
        sems = [s.strip() for s in sem.split("&")]
    elif "," in sem:
        sems = [s.strip() for s in sem.split(",")]
    else:
        sems = [sem]
    
    return branch, sems

def load_courses(csv_path):
    """
    Reads courses CSV with format: Course code, Course Name, branch, semester, LTPSC, faculty, strength, type
    """
    courses_dict = {}
    normalized = []

    if not os.path.exists(csv_path):
        messagebox.showerror("Error", f"File not found: {csv_path}")
        return [], {}

    try:
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            # Try to detect delimiter
            sample = f.read(1024)
            f.seek(0)
            delimiter = ',' if ',' in sample else '\t'
            
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                messagebox.showerror("Error", "Empty or invalid CSV file for courses.")
                return [], {}

            # Normalize column names
            fieldnames = [f.strip().lower() for f in reader.fieldnames]
            reader.fieldnames = fieldnames
            
            # Map expected columns
            code_col = _pick_column(fieldnames, ["course code", "course_code", "code"])
            name_col = _pick_column(fieldnames, ["course name", "course_name", "name", "title"])
            branch_col = _pick_column(fieldnames, ["branch", "department", "dept"])
            sem_col = _pick_column(fieldnames, ["semester", "sem"])
            ltp_col = _pick_column(fieldnames, ["ltpsc", "l-t-p-s-c", "ltp"])
            faculty_col = _pick_column(fieldnames, ["faculty", "teacher", "instructor"])
            strength_col = _pick_column(fieldnames, ["strength", "students", "no. of students"])
            type_col = _pick_column(fieldnames, ["type", "course type"])

            required_cols = [code_col, name_col, branch_col, sem_col, ltp_col]
            if not all(required_cols):
                messagebox.showerror("Error", "Courses CSV missing required columns")
                return [], {}

            for row_num, row in enumerate(reader, 2):
                try:
                    code = str(row[code_col]).strip()
                    name = str(row[name_col]).strip()
                    branch_raw = str(row[branch_col]).strip()
                    sem_raw = str(row[sem_col]).strip()
                    ltp_raw = str(row[ltp_col]).strip()
                    faculty = str(row[faculty_col]).strip() if faculty_col else ""
                    strength = _safe_int(row[strength_col]) if strength_col else 0
                    course_type = str(row[type_col]).strip().lower() if type_col else "core"

                    if not code or not name:
                        continue

                    # Parse branch and semester
                    branch, semesters = parse_branch_semester(branch_raw, sem_raw)
                    
                    # Parse L-T-P-S-C
                    lecture_hours, tutorial_hours, lab_hours = parse_ltpsc(ltp_raw)

                    # Handle CSE sections
                    if branch == "CSE" and "(separate)" in branch_raw:
                        # Create entries for both sections with different faculties
                        faculties = [f.strip() for f in faculty.split(",")] if "," in faculty else [faculty, faculty]
                        for i, section in enumerate(["CSE-A", "CSE-B"]):
                            section_faculty = faculties[i] if i < len(faculties) else faculties[0]
                            
                            courses_dict.setdefault(section, {}).setdefault(sem, {})
                            courses_dict[section][sem][code] = {
                                "name": name,
                                "faculty": section_faculty,
                                "class_room": "",
                                "lab_room": "",
                                "lecture_hours": lecture_hours,
                                "tutorial_hours": tutorial_hours,
                                "lab_hours": lab_hours,
                                "students": strength // 2 if strength > 0 else 0,
                                "type": course_type,
                                "original_branch": branch
                            }
                            normalized.append({
                                "code": code, "name": name, "branch": section, "semester": sem,
                                "faculty": section_faculty, "students": strength // 2,
                                "lecture_hours": lecture_hours, "tutorial_hours": tutorial_hours, 
                                "lab_hours": lab_hours, "type": course_type
                            })

                    elif branch == "CSE" and "(combined)" in branch_raw:
                        # Create linked entries for combined course
                        for section in ["CSE-A", "CSE-B"]:
                            courses_dict.setdefault(section, {}).setdefault(sem, {})
                            courses_dict[section][sem][code] = {
                                "name": name,
                                "faculty": faculty,
                                "class_room": "",
                                "lab_room": "",
                                "lecture_hours": lecture_hours,
                                "tutorial_hours": tutorial_hours,
                                "lab_hours": lab_hours,
                                "students": strength,
                                "type": course_type,
                                "linked_pair": ("CSE-A" if section == "CSE-B" else "CSE-B", sem, code),
                                "original_branch": branch
                            }
                        normalized.append({
                            "code": code, "name": name, "branch": "CSE-COMBINED", "semester": sem,
                            "faculty": faculty, "students": strength,
                            "lecture_hours": lecture_hours, "tutorial_hours": tutorial_hours, 
                            "lab_hours": lab_hours, "type": course_type
                        })

                    else:
                        # Regular course for all semesters
                        for sem in semesters:
                            courses_dict.setdefault(branch, {}).setdefault(sem, {})
                            courses_dict[branch][sem][code] = {
                                "name": name,
                                "faculty": faculty,
                                "class_room": "",
                                "lab_room": "",
                                "lecture_hours": lecture_hours,
                                "tutorial_hours": tutorial_hours,
                                "lab_hours": lab_hours,
                                "students": strength,
                                "type": course_type,
                                "original_branch": branch
                            }
                            normalized.append({
                                "code": code, "name": name, "branch": branch, "semester": sem,
                                "faculty": faculty, "students": strength,
                                "lecture_hours": lecture_hours, "tutorial_hours": tutorial_hours, 
                                "lab_hours": lab_hours, "type": course_type
                            })

                except Exception as e:
                    print(f"Warning: Error processing row {row_num}: {e}")
                    continue

        messagebox.showinfo("Success", f"Loaded {len(normalized)} course entries")
        return normalized, courses_dict

    except Exception as e:
        messagebox.showerror("Error", f"Failed to read courses CSV:\n{e}")
        return [], {}