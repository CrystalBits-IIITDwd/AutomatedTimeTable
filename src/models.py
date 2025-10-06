# models.py
class Course:
    """
    Flexible Course model that supports either:
      - Course(code, name, faculty, room, hours_per_week, branch, semester)
      - Course(code, name, faculty, room, lecture_hours, tutorial_hours, lab_hours, branch, semester)
    Also accepts keyword args: lecture_hours, tutorial_hours, lab_hours, branch, semester.
    Always exposes .lecture_hours, .tutorial_hours, .lab_hours and .hours_per_week.
    """
    def __init__(self, code, name, faculty, room, *args, **kwargs):
        self.code = code
        self.name = name
        self.faculty = faculty
        self.room = room

        # defaults
        self.lecture_hours = 0
        self.tutorial_hours = 0
        self.lab_hours = 0
        self.branch = kwargs.get("branch")
        self.semester = kwargs.get("semester")

        # 1) form: (hours_per_week, branch, semester)
        if len(args) == 3 and (isinstance(args[0], (int, str)) and isinstance(args[1], str) and isinstance(args[2], str)):
            hours_per_week = int(args[0])
            self.lecture_hours = hours_per_week
            self.tutorial_hours = 0
            self.lab_hours = 0
            self.branch = args[1]
            self.semester = args[2]
            self.hours_per_week = hours_per_week

        # 2) form: (lecture_hours, tutorial_hours, lab_hours, branch, semester)
        elif len(args) == 5:
            self.lecture_hours = int(args[0])
            self.tutorial_hours = int(args[1])
            self.lab_hours = int(args[2])
            self.branch = args[3]
            self.semester = args[4]
            self.hours_per_week = self.lecture_hours + self.tutorial_hours + self.lab_hours

        else:
            # fall back to kwargs
            if "lecture_hours" in kwargs:
                self.lecture_hours = int(kwargs["lecture_hours"])
            if "tutorial_hours" in kwargs:
                self.tutorial_hours = int(kwargs["tutorial_hours"])
            if "lab_hours" in kwargs:
                self.lab_hours = int(kwargs["lab_hours"])
            if "branch" in kwargs:
                self.branch = kwargs["branch"]
            if "semester" in kwargs:
                self.semester = kwargs["semester"]
            self.hours_per_week = self.lecture_hours + self.tutorial_hours + self.lab_hours

        # normalize branch/semester to strings if present
        if self.branch is not None:
            self.branch = str(self.branch)
        if self.semester is not None:
            self.semester = str(self.semester)

    def __repr__(self):
        return f"{self.code} - {self.name} ({self.faculty})"
