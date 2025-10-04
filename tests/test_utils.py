import pytest
from src.utils import SLOTS

def test_slots():
    slots = SLOTS
    # Must not be empty
    assert len(slots) > 0
    # All slots should contain "-"
    assert all("-" in slot for slot in slots)
    # Optional: check slot format HH:MM-HH:MM
    for slot in slots:
        start, end = slot.split("-")
        sh, sm = map(int, start.split(":"))
        eh, em = map(int, end.split(":"))
        assert 0 <= sh < 24 and 0 <= sm < 60
        assert 0 <= eh < 24 and 0 <= em < 60
