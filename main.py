# temporary "testing ground" to verify your logic works in the terminal

from petnest_system import Owner, Pet, Task, Scheduler

# ── 1. Create an Owner ──────────────────────────────────────────────────────
owner = Owner(
    name="Alex",
    time_available=120,
    preferences={"prefer_morning": True}
)

# ── 2. Create two Pets ──────────────────────────────────────────────────────
buddy    = Pet(name="Buddy",    species="dog", age=3, health_notes="No known allergies")
whiskers = Pet(name="Whiskers", species="cat", age=5, health_notes="Sensitive stomach — grain-free food only")

# ── 3. Add Tasks (some intentionally at the same time to trigger conflicts) ─
# Buddy's tasks
buddy.add_task(Task("Evening fetch",  "exercise",   20, "medium", "evening",   pet_name="Buddy",    time="18:30"))
buddy.add_task(Task("Morning walk",   "exercise",   30, "high",   "morning",   pet_name="Buddy",    time="07:00"))
buddy.add_task(Task("Afternoon nap",  "rest",       15, "low",    "afternoon", pet_name="Buddy",    time="13:00"))
buddy.add_task(Task("Breakfast",      "feeding",    10, "high",   "morning",   pet_name="Buddy",    time="08:00"))

# Whiskers' tasks — "Breakfast" and "Medication dose" clash with Buddy's times
whiskers.add_task(Task("Play session",    "exercise",   15, "low",    "afternoon", pet_name="Whiskers", time="15:00"))
whiskers.add_task(Task("Breakfast",       "feeding",    10, "high",   "morning",   pet_name="Whiskers", time="08:00"))  # same as Buddy's Breakfast
whiskers.add_task(Task("Medication dose", "medication",  5, "high",   "afternoon", pet_name="Whiskers", time="13:00"))  # same as Buddy's Afternoon nap

# ── 4. Detect conflicts across all tasks ────────────────────────────────────
all_tasks = buddy.tasks + whiskers.tasks
owner.add_pet(buddy)           # need a pet assigned to build a Scheduler
scheduler = Scheduler(owner)

print("=" * 55)
print("         CONFLICT DETECTION DEMO")
print("=" * 55)

conflicts = scheduler.detect_conflicts(all_tasks)

if conflicts:
    for warning in conflicts:
        print(warning)
else:
    print("No conflicts found.")

# ── 5. Sort all tasks by time and display ───────────────────────────────────
print("\n" + "=" * 55)
print("         ALL TASKS SORTED BY TIME")
print("=" * 55)
sorted_tasks = scheduler.sort_by_time(all_tasks)
for task in sorted_tasks:
    print(f"  {task.time}  [{task.pet_name:<8}]  {task.name}")

# ── 6. Filter demos ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("         FILTER: Buddy's tasks only")
print("=" * 55)
buddy_tasks = scheduler.filter_tasks(all_tasks, pet_name="Buddy")
for t in buddy_tasks:
    print(f"  {t.time}  {t.name}")

print("\n" + "=" * 55)
