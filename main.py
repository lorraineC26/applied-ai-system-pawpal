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

# ── 3. Add Tasks to each Pet ────────────────────────────────────────────────
# Buddy's tasks
buddy.add_task(Task("Morning walk",   "exercise",   30, "high",   "morning"))
buddy.add_task(Task("Breakfast",      "feeding",    10, "high",   "morning"))
buddy.add_task(Task("Evening fetch",  "exercise",   20, "medium", "evening"))

# Whiskers' tasks
whiskers.add_task(Task("Breakfast",        "feeding",    10, "high",   "morning"))
whiskers.add_task(Task("Medication dose",  "medication", 5,  "high",   "afternoon"))
whiskers.add_task(Task("Play session",     "exercise",   15, "low",    "afternoon"))

# ── 4. Print Today's Schedule ───────────────────────────────────────────────
print("=" * 50)
print("          TODAY'S PAWPAL SCHEDULE")
print("=" * 50)
print(f"Owner: {owner.name}  |  Time available: {owner.time_available} min\n")

for pet in [buddy, whiskers]:
    owner.add_pet(pet)          # assign pet so Scheduler can access it
    scheduler = Scheduler(owner)
    schedule = scheduler.generate_schedule()

    print(f"  {pet.name} ({pet.species}, age {pet.age})")
    print(f"  Health notes: {pet.health_notes}")
    print(f"  {'-' * 44}")

    for i, task in enumerate(schedule.tasks, 1):
        status = "[done]" if task.completed else "[ ]"
        print(f"  {i}. {status} [{task.preferred_time:<9}] {task.name:<20} "
              f"{task.duration:>3} min  |  {task.priority} priority")

    print(f"\n  Total scheduled: {schedule.total_duration} min")
    print()

print("=" * 50)
