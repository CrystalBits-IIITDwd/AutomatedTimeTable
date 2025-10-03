import pytest
from src.utils import generate_slots

def test_generate_slots():
    slots = generate_slots()
    # Must not be empty
    assert len(slots) > 0
    # All slots should contain "-"
    assert all("-" in slot for slot in slots)
    # Check if lunch break is avoided
    for slot in slots:
        assert "13:15" not in slot and "14:00" not in slot
