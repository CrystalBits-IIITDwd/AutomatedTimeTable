# models.py
class Course:
    def __init__(self, code, name, faculty, room,
                 lecture_hours, tutorial_hours, lab_hours,
                 branch, semester):
        self.code = code
        self.name = name
        self.faculty = faculty
        self.room = room
        self.lecture_hours = int(lecture_hours)
        self.tutorial_hours = int(tutorial_hours)
        self.lab_hours = int(lab_hours)
        self.branch = branch
        self.semester = semester

    def __repr__(self):
        return f"{self.code} - {self.name} ({self.faculty})"
