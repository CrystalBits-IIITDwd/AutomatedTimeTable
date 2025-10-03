import pytest
from src.scheduler import TimetableScheduler

def test_scheduler_no_collision():
    scheduler = TimetableScheduler()

    # Add two courses in same room different times
    scheduler.add_course("CSE", "3", "CS301", "Networks", "Prof A", "C205", 1)
    scheduler.add_course("CSE", "5", "CS501", "Software", "Prof B", "C205", 1)

    timetable, unscheduled = scheduler.generate_timetable()

    # Same room shouldn't collide in same slot
    occupied = {}
    for (day, slot), (_, _, room) in timetable["CSE"]["3"].items():
        assert (day, slot, room) not in occupied
        occupied[(day, slot, room)] = True
    for (day, slot), (_, _, room) in timetable["CSE"]["5"].items():
        assert (day, slot, room) not in occupied
        occupied[(day, slot, room)] = True

    assert len(unscheduled) == 0
