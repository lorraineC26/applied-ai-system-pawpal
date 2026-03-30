import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pawpal_system import Task, Pet


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
