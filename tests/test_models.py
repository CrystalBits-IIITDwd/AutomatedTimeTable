from src.models import Course

def test_course_creation():
    course = Course("CS101", "Intro to CS", "Prof X", "C101", 3, "CSE", "1")
    assert course.code == "CS101"
    assert course.name == "Intro to CS"
    assert course.faculty == "Prof X"
    assert course.room == "C101"
    assert course.hours_per_week == 3
    assert course.branch == "CSE"
    assert course.semester == "1"
