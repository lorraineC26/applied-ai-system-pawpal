import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import date, timedelta
from petnest_system import Task, Pet, Owner, Scheduler


def test_task_completion():
    """Calling mark_complete() should flip completed from False to True."""
    task = Task("Morning walk", "exercise", 30, "high", "morning")
    assert task.completed == False
    task.mark_complete()
    assert task.completed == True


def test_task_addition_increases_count():
    """Adding a task to a Pet should increase its task count by 1."""
    pet = Pet("Buddy", "dog", 3, "No allergies")
    assert len(pet.tasks) == 0
    pet.add_task(Task("Breakfast", "feeding", 10, "high", "morning"))
    assert len(pet.tasks) == 1


# ---------------------------------------------------------------------------
# Sorting correctness
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """sort_by_time returns tasks ordered earliest to latest HH:MM."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Evening walk",  "exercise", 30, "low",  "evening",  time="18:00"),
        Task("Morning meds",  "medication", 5, "high", "morning",  time="07:30"),
        Task("Afternoon feed","feeding",   15, "medium","afternoon",time="12:00"),
    ]

    sorted_tasks = scheduler.sort_by_time(tasks)
    times = [t.time for t in sorted_tasks]
    assert times == ["07:30", "12:00", "18:00"]


def test_sort_by_time_already_sorted():
    """sort_by_time is stable when tasks are already in order."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("A", "exercise", 10, "low", "morning", time="08:00"),
        Task("B", "feeding",  10, "low", "morning", time="09:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    assert [t.name for t in sorted_tasks] == ["A", "B"]


def test_sort_by_time_same_time_stable():
    """Tasks sharing the same time value stay together (no crash, order preserved)."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Walk",  "exercise", 20, "high", "morning", time="08:00"),
        Task("Feed",  "feeding",  10, "high", "morning", time="08:00"),
        Task("Brush", "grooming",  5, "low",  "morning", time="07:00"),
    ]
    sorted_tasks = scheduler.sort_by_time(tasks)
    # Brush (07:00) must come first; Walk and Feed (08:00) follow
    assert sorted_tasks[0].time == "07:00"
    assert sorted_tasks[1].time == "08:00"
    assert sorted_tasks[2].time == "08:00"


# ---------------------------------------------------------------------------
# Recurrence logic
# ---------------------------------------------------------------------------

def test_daily_recurrence_next_day():
    """Completing a daily task returns a new task scheduled for the next calendar day."""
    today = date.today().isoformat()
    task = Task("Daily walk", "exercise", 30, "high", "morning",
                recurrence="daily", due_date=today)

    next_task = task.mark_complete()

    assert task.completed is True
    assert next_task is not None
    expected = (date.today() + timedelta(days=1)).isoformat()
    assert next_task.due_date == expected
    assert next_task.recurrence == "daily"
    assert next_task.name == task.name


def test_weekly_recurrence_next_week():
    """Completing a weekly task returns a new task scheduled seven days later."""
    today = date.today().isoformat()
    task = Task("Weekly bath", "grooming", 45, "medium", "morning",
                recurrence="weekly", due_date=today)

    next_task = task.mark_complete()

    assert next_task is not None
    expected = (date.today() + timedelta(weeks=1)).isoformat()
    assert next_task.due_date == expected
    assert next_task.recurrence == "weekly"


def test_non_recurring_returns_none():
    """Completing a task with no recurrence returns None."""
    task = Task("Vet visit", "medical", 60, "high", "morning")
    result = task.mark_complete()
    assert result is None
    assert task.completed is True


def test_daily_recurrence_preserves_attributes():
    """The spawned recurring task keeps all original attributes intact."""
    task = Task("Morning meds", "medication", 5, "high", "morning",
                pet_name="Luna", time="08:00", recurrence="daily")

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.category == "medication"
    assert next_task.duration == 5
    assert next_task.priority == "high"
    assert next_task.pet_name == "Luna"
    assert next_task.time == "08:00"
    assert next_task.completed is False   # new task starts incomplete


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_detect_conflicts_flags_same_time():
    """Two tasks at the same time should produce one conflict warning."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Walk",  "exercise", 20, "high", "morning", time="09:00"),
        Task("Feed",  "feeding",  10, "high", "morning", time="09:00"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert len(warnings) == 1
    assert "09:00" in warnings[0]
    assert "WARNING" in warnings[0]


def test_detect_conflicts_no_overlap_returns_empty():
    """Tasks at distinct times should produce no warnings."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Walk",  "exercise", 20, "high", "morning",   time="08:00"),
        Task("Feed",  "feeding",  10, "medium","afternoon", time="12:00"),
        Task("Brush", "grooming",  5, "low",  "evening",   time="18:00"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert warnings == []


def test_detect_conflicts_multiple_slots():
    """Multiple conflicting time slots each produce their own warning."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Walk A",  "exercise", 20, "high", "morning",   time="09:00"),
        Task("Walk B",  "exercise", 20, "high", "morning",   time="09:00"),
        Task("Feed A",  "feeding",  10, "medium","afternoon", time="13:00"),
        Task("Feed B",  "feeding",  10, "medium","afternoon", time="13:00"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert len(warnings) == 2


def test_detect_conflicts_includes_pet_name():
    """Conflict warning should include pet names when present."""
    owner = Owner("Alex", 120, {})
    scheduler = Scheduler(owner)

    tasks = [
        Task("Walk", "exercise", 20, "high", "morning", pet_name="Buddy", time="09:00"),
        Task("Feed", "feeding",  10, "high", "morning", pet_name="Luna",  time="09:00"),
    ]
    warnings = scheduler.detect_conflicts(tasks)
    assert "Buddy" in warnings[0]
    assert "Luna"  in warnings[0]
