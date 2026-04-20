# PawPal+ (Module 2 Project)

## Features

**Priority-based greedy scheduling** — `Scheduler.generate_schedule()` sorts all tasks by a three-key comparator: priority tier (high → medium → low), then preferred time slot (morning → afternoon → evening → any), then duration (shorter tasks break ties). It then walks the sorted list once and greedily accepts each task only if it fits within the owner's remaining time budget, recording an inclusion or exclusion reason for every task.

**Chronological sort** — `Scheduler.sort_by_time(tasks)` orders tasks by their `HH:MM` scheduled-time attribute using Python's built-in lexicographic string sort. Zero-padded `HH:MM` strings compare correctly without any parsing or conversion.

**Multi-criteria filter** — `Scheduler.filter_tasks(tasks, completed, pet_name)` composes up to two independent predicates: one for completion status (`True` / `False` / `None` for all) and one for pet name. Each active predicate is applied as a list comprehension in sequence, so either, both, or neither filter can be omitted.

**Scheduling conflict detection** — `Scheduler.detect_conflicts(tasks)` uses a `collections.defaultdict` to bucket tasks by their `time` value. Any bucket with two or more tasks produces a `WARNING` string that names every conflicting task (with its pet's name when present). The method always returns a list and never raises, so the UI can surface warnings without interrupting the user's workflow.

**Recurring task generation** — `Task.mark_complete()` marks the current task done and, for tasks with `recurrence="daily"` or `recurrence="weekly"`, returns a new `Task` instance with the same attributes but `due_date` advanced by `timedelta(days=1)` or `timedelta(weeks=1)` and `completed` reset to `False`. Non-recurring tasks return `None`.

---

## 📸 Demo

![PawPal+ app screenshot](public/task.png)
![PawPal+ app screenshot](public/task2.png)
![PawPal+ app screenshot](public/task3.png)
![PawPal+ app screenshot](public/task4.png)

---

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Smarter Scheduling

The `Scheduler` class has been extended with three features beyond basic plan generation:

**Sort by time** — `sort_by_time(tasks)` returns tasks ordered chronologically using each task's `time` attribute in `HH:MM` format. Because the strings are zero-padded, standard string comparison produces the correct order with no conversion needed.

**Filter tasks** — `filter_tasks(tasks, completed, pet_name)` returns a subset of tasks matching the given criteria. Both parameters are optional, so you can filter by completion status, by pet name, or both at once.

**Conflict detection** — `detect_conflicts(tasks)` scans a task list for two or more tasks scheduled at the same time. It returns a list of warning strings (one per conflict) rather than raising an exception, so the app can surface warnings without interrupting the user's workflow.

**Recurring tasks** — `Task` now accepts a `recurrence` field (`"daily"` or `"weekly"`). When `mark_complete()` is called on a recurring task, it returns a new `Task` instance due on the next occurrence, calculated with Python's `timedelta`. Non-recurring tasks return `None`.

## Testing PawPal+

### Run the test suite

```bash
python3.9 -m pytest tests/test_pawpal.py -v
```

Or, if your environment has `pytest` on the default `python`:

```bash
python -m pytest tests/test_pawpal.py -v
```

### What the tests cover

| Area | What is verified |
|---|---|
| **Task completion** | `mark_complete()` flips `completed` to `True` |
| **Pet task list** | `add_task()` increases the pet's task count |
| **Sorting** | `sort_by_time()` returns tasks in chronological `HH:MM` order; handles already-sorted lists and ties without crashing |
| **Recurrence — daily** | Completing a daily task returns a new task due the next calendar day with all attributes preserved and `completed = False` |
| **Recurrence — weekly** | Completing a weekly task returns a new task due seven days later |
| **Recurrence — none** | Completing a non-recurring task returns `None` |
| **Conflict detection** | Flags two or more tasks at the same time with a `WARNING` string; returns `[]` when no overlaps exist; handles multiple conflicting slots; includes pet names in the warning message |

13 tests, 0 failures.

### Confidence Level

★★★★☆ (4 / 5)

The core scheduling behaviors — sorting, recurrence, and conflict detection — are fully tested and all pass. One star is held back because the tests cover the logic layer only; the Streamlit UI (`app.py`) and the `generate_schedule` time-budget enforcement are not yet covered by automated tests, so end-to-end reliability has not been verified.

---

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
