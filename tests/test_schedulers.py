from src.scheduler import TimetableScheduler

def _to_minutes(slot):
    s, e = slot.split("-")
    sh, sm = map(int, s.split(":"))
    eh, em = map(int, e.split(":"))
    return sh * 60 + sm, eh * 60 + em

def test_scheduler_no_room_overlap():
    scheduler = TimetableScheduler()

    # Add two courses placed in same room but different semesters
    scheduler.add_course("CSE", "3", "CS301", "Networks", "Prof A", "C205", 1)
    scheduler.add_course("CSE", "5", "CS501", "Software", "Prof B", "C205", 1)

    timetable, unscheduled = scheduler.generate_timetable(notify=False)

    # Build assignments per (room, day) and ensure no overlapping intervals
    assignments = {}  # (room, day) -> list of (start, end)
    for branch in timetable:
        for sem in timetable[branch]:
            # scheduler stores (code, name, faculty, type, room)
            for (day, slot), (_, _, _, _, room) in timetable[branch][sem].items():
                s, e = _to_minutes(slot)
                key = (room, day)
                if key not in assignments:
                    assignments[key] = []
                # ensure no overlap with existing intervals
                for (os, oe) in assignments[key]:
                    assert oe <= s or e <= os
                assignments[key].append((s, e))

    assert len(unscheduled) == 0
