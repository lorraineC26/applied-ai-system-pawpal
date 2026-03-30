# "logic layer" where all your backend classes live

class Task:
    def __init__(self, name, category, duration, priority, preferred_time):
        """Create a new Task with a name, category, duration, priority, and preferred time."""
        self.name = name                    # e.g. "Morning walk"
        self.category = category            # e.g. "exercise", "feeding", "medication"
        self.duration = duration            # in minutes
        self.priority = priority            # "low", "medium", or "high"
        self.preferred_time = preferred_time  # e.g. "morning", "afternoon", "evening"
        self.completed = False

    def mark_complete(self):
        """Mark this task as completed."""
        self.completed = True

    def edit(self, field, value):
        """Update a field on the task by name."""
        if hasattr(self, field):
            setattr(self, field, value)
        else:
            raise ValueError(f"Task has no field '{field}'")

    def to_dict(self):
        """Return task data as a plain dictionary (useful for display/export)."""
        return {
            "name": self.name,
            "category": self.category,
            "duration": self.duration,
            "priority": self.priority,
            "preferred_time": self.preferred_time,
            "completed": self.completed,
        }

    def __repr__(self):
        """Return a debug-friendly string representation of the Task."""
        return f"Task({self.name!r}, priority={self.priority}, duration={self.duration}min)"


class Pet:
    def __init__(self, name, species, age, health_notes):
        """Create a new Pet with basic profile info and an empty task list."""
        self.name = name
        self.species = species      # e.g. "dog", "cat"
        self.age = age              # in years
        self.health_notes = health_notes  # free-text notes (allergies, conditions, etc.)
        self.tasks = []             # Pet "1" --> "*" Task

    def add_task(self, task):
        """Add a Task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_name):
        """Remove a task by name. Returns True if found and removed."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.name != task_name]
        return len(self.tasks) < before

    def get_profile(self):
        """Return a summary dict of the pet's info and task count."""
        return {
            "name": self.name,
            "species": self.species,
            "age": self.age,
            "health_notes": self.health_notes,
            "task_count": len(self.tasks),
        }

    def __repr__(self):
        """Return a debug-friendly string representation of the Pet."""
        return f"Pet({self.name!r}, {self.species}, age={self.age})"


class Owner:
    def __init__(self, name, time_available, preferences):
        """Create a new Owner with a name, daily time budget, and scheduling preferences."""
        self.name = name
        self.time_available = time_available  # total minutes available today
        self.preferences = preferences        # dict, e.g. {"prefer_morning": True}
        self.pet = None                       # Owner "1" --> "1" Pet
        self.tasks = []                       # flat list kept in sync with pet tasks

    def add_pet(self, pet):
        """Assign a pet to this owner and sync the task list."""
        self.pet = pet
        self.tasks = pet.tasks  # shared reference — changes to pet.tasks reflect here

    def get_summary(self):
        """Return a human-readable summary of the owner, their pet, and tasks."""
        pet_info = self.pet.get_profile() if self.pet else "No pet assigned"
        return {
            "owner": self.name,
            "time_available_minutes": self.time_available,
            "preferences": self.preferences,
            "pet": pet_info,
            "total_tasks": len(self.tasks),
        }

    def __repr__(self):
        """Return a debug-friendly string representation of the Owner."""
        return f"Owner({self.name!r}, time_available={self.time_available}min)"


class Schedule:
    PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
    TIME_SLOTS = ["morning", "afternoon", "evening", "any"]

    def __init__(self, date, tasks, total_duration, reasoning):
        """Create a Schedule with an ordered task list, total duration, and per-task reasoning."""
        self.date = date                    # date string, e.g. "2026-03-29"
        self.tasks = tasks                  # ordered list of Task objects
        self.total_duration = total_duration  # sum of durations (minutes)
        self.reasoning = reasoning          # dict mapping task name -> reason string

    def display(self):
        """Print a formatted schedule to the console."""
        print(f"\n=== Schedule for {self.date} ===")
        print(f"Total time: {self.total_duration} min\n")
        for i, task in enumerate(self.tasks, 1):
            reason = self.reasoning.get(task.name, "")
            print(f"{i}. [{task.preferred_time}] {task.name} ({task.duration} min, {task.priority} priority)")
            if reason:
                print(f"   Reason: {reason}")
        print()

    def get_reasoning(self):
        """Return the reasoning dictionary."""
        return self.reasoning

    def to_dict_list(self):
        """Return schedule as a list of dicts (useful for Streamlit tables)."""
        rows = []
        for task in self.tasks:
            rows.append({
                "Task": task.name,
                "Category": task.category,
                "Duration (min)": task.duration,
                "Priority": task.priority,
                "Time of Day": task.preferred_time,
                "Reason": self.reasoning.get(task.name, ""),
            })
        return rows

    def __repr__(self):
        """Return a debug-friendly string representation of the Schedule."""
        return f"Schedule(date={self.date!r}, tasks={len(self.tasks)}, total={self.total_duration}min)"


class Scheduler:
    PRIORITY_WEIGHT = {"high": 3, "medium": 2, "low": 1}

    def __init__(self, owner):
        """Create a Scheduler tied to a specific Owner."""
        self.owner = owner
        self.schedule = None  # set after generate_schedule() is called

    def generate_schedule(self):
        """
        Build a daily Schedule by:
        1. Sorting tasks by priority (high first), then preferred time slot.
        2. Fitting tasks within the owner's available time budget.
        3. Recording a reason for each included (or excluded) task.
        Returns a Schedule object.
        """
        if not self.owner.pet:
            raise ValueError("Owner has no pet assigned.")

        all_tasks = self.owner.tasks
        time_budget = self.owner.time_available
        prefer_morning = self.owner.preferences.get("prefer_morning", False)

        # Sort: priority first, then time-slot order, then duration (shorter first as tiebreak)
        time_slot_order = {"morning": 0, "afternoon": 1, "evening": 2, "any": 3}

        def sort_key(task):
            slot = time_slot_order.get(task.preferred_time, 3)
            # If owner prefers morning, bump morning tasks higher
            if prefer_morning and task.preferred_time == "morning":
                slot = -1
            return (Schedule.PRIORITY_ORDER.get(task.priority, 2), slot, task.duration)

        sorted_tasks = sorted(all_tasks, key=sort_key)

        chosen = []
        reasoning = {}
        time_used = 0

        for task in sorted_tasks:
            if time_used + task.duration <= time_budget:
                chosen.append(task)
                time_used += task.duration
                reasoning[task.name] = (
                    f"Included — {task.priority} priority, fits within available time "
                    f"({task.duration} min, preferred time: {task.preferred_time})."
                )
            else:
                reasoning[task.name] = (
                    f"Skipped — not enough time remaining "
                    f"({task.duration} min needed, {time_budget - time_used} min left)."
                )

        self.schedule = Schedule(
            date=self._today(),
            tasks=chosen,
            total_duration=time_used,
            reasoning=reasoning,
        )
        return self.schedule

    def explain_plan(self):
        """Print a plain-English explanation of the current schedule."""
        if not self.schedule:
            print("No schedule generated yet. Call generate_schedule() first.")
            return
        print(f"\n=== Plan Explanation for {self.owner.name}'s pet {self.owner.pet.name} ===")
        print(f"Available time: {self.owner.time_available} min | Scheduled: {self.schedule.total_duration} min\n")
        for task_name, reason in self.schedule.reasoning.items():
            print(f"• {task_name}: {reason}")
        print()

    @staticmethod
    def _today():
        """Return today's date as a string."""
        from datetime import date
        return date.today().isoformat()

    def __repr__(self):
        """Return a debug-friendly string representation of the Scheduler."""
        return f"Scheduler(owner={self.owner.name!r})"
