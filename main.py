# temporary "testing ground" to verify your logic works in the terminal

from pawpal_system import Owner, Pet, Task, Scheduler

# ── 1. Create an Owner ──────────────────────────────────────────────────────
owner = Owner(
    name="Alex",
    time_available=120,
    preferences={"prefer_morning": True}
)

# ── 2. Create two Pets ──────────────────────────────────────────────────────
buddy = Pet(name="Buddy", species="dog", age=3, health_notes="No known allergies")
whiskers = Pet(name="Whiskers", species="cat", age=5, health_notes="Sensitive stomach — grain-free food only")

# ── 3. Add Tasks OUT OF ORDER (by time) ────────────────────────────────────
# Buddy's tasks — intentionally added out of chronological order
buddy.add_task(Task("Evening fetch",  "exercise",   20, "medium", "evening",   pet_name="Buddy", time="18:30"))
buddy.add_task(Task("Morning walk",   "exercise",   30, "high",   "morning",   pet_name="Buddy", time="07:00"))
buddy.add_task(Task("Afternoon nap",  "rest",       15, "low",    "afternoon", pet_name="Buddy", time="13:00"))
buddy.add_task(Task("Breakfast",      "feeding",    10, "high",   "morning",   pet_name="Buddy", time="08:00"))

# Whiskers' tasks — also out of order
whiskers.add_task(Task("Play session",     "exercise",   15, "low",    "afternoon", pet_name="Whiskers", time="15:00"))
whiskers.add_task(Task("Breakfast",        "feeding",    10, "high",   "morning",   pet_name="Whiskers", time="07:30"))
whiskers.add_task(Task("Medication dose",  "medication",  5, "high",   "afternoon", pet_name="Whiskers", time="12:00"))

# Mark a couple tasks complete for filter demo
buddy.tasks[1].mark_complete()    # Morning walk → done
whiskers.tasks[2].mark_complete() # Medication dose → done

# ── 4. Demonstrate sort_by_time() ───────────────────────────────────────────
print("=" * 50)
print("         SORT BY TIME DEMO")
print("=" * 50)

for pet in [buddy, whiskers]:
    print(f"\n{pet.name}'s tasks sorted by time:")
    owner.add_pet(pet)
    scheduler = Scheduler(owner)
    sorted_tasks = scheduler.sort_by_time(pet.tasks)
    for task in sorted_tasks:
        status = "[done]" if task.completed else "[ ]"
        print(f"  {task.time}  {status}  {task.name}")

# ── 5. Demonstrate filter_tasks() ───────────────────────────────────────────
all_tasks = buddy.tasks + whiskers.tasks

print("\n" + "=" * 50)
print("         FILTER DEMO")
print("=" * 50)

# Filter: incomplete tasks only
incomplete = scheduler.filter_tasks(all_tasks, completed=False)
print(f"\nIncomplete tasks ({len(incomplete)}):")
for t in incomplete:
    print(f"  [ ]  [{t.pet_name}]  {t.name}")

# Filter: completed tasks only
done = scheduler.filter_tasks(all_tasks, completed=True)
print(f"\nCompleted tasks ({len(done)}):")
for t in done:
    print(f"  [done]  [{t.pet_name}]  {t.name}")

# Filter: Buddy's tasks only
buddy_tasks = scheduler.filter_tasks(all_tasks, pet_name="Buddy")
print(f"\nBuddy's tasks only ({len(buddy_tasks)}):")
for t in buddy_tasks:
    print(f"  {t.time}  {t.name}")

# Filter: Whiskers' incomplete tasks
whiskers_incomplete = scheduler.filter_tasks(all_tasks, completed=False, pet_name="Whiskers")
print(f"\nWhiskers' incomplete tasks ({len(whiskers_incomplete)}):")
for t in whiskers_incomplete:
    print(f"  {t.time}  {t.name}")

print("\n" + "=" * 50)
