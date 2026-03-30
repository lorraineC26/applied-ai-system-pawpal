# PawPal+ (Module 2 Project)

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
