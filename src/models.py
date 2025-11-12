# models.py
class Course:
    """
    Flexible Course model kept for compatibility.
    """
    def __init__(self, code, name, faculty, room, *args, **kwargs):
        self.code = code
        self.name = name
        self.faculty = faculty
        self.room = room

        self.lecture_hours = 0
        self.tutorial_hours = 0
        self.lab_hours = 0
        self.branch = kwargs.get("branch")
        self.semester = kwargs.get("semester")

        if len(args) == 3:
            hours_per_week = int(args[0])
            self.lecture_hours = hours_per_week
            self.hours_per_week = hours_per_week
            self.branch = args[1]
            self.semester = args[2]
        elif len(args) == 5:
            self.lecture_hours = int(args[0])
            self.tutorial_hours = int(args[1])
            self.lab_hours = int(args[2])
            self.branch = args[3]
            self.semester = args[4]
            self.hours_per_week = self.lecture_hours + self.tutorial_hours + self.lab_hours
        else:
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

        if self.branch is not None:
            self.branch = str(self.branch)
        if self.semester is not None:
            self.semester = str(self.semester)

        self.class_room = kwargs.get("class_room", self.room)
        self.lab_room = kwargs.get("lab_room", "")

    def __repr__(self):
        return f"{self.code} - {self.name} ({self.faculty})"
