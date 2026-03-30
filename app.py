import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

# --- Session state: create objects once, reuse them on every rerun ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(owner_name, time_available=120, preferences={"prefer_morning": True})

if "pet" not in st.session_state:
    st.session_state.pet = Pet(pet_name, species, age=3, health_notes="")
    st.session_state.owner.add_pet(st.session_state.pet)

if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)

if "schedule_stale" not in st.session_state:
    st.session_state.schedule_stale = False

# Sync widget values to existing objects on every rerun
st.session_state.owner.name = owner_name
st.session_state.pet.name = pet_name
st.session_state.pet.species = species

st.markdown("### Tasks")
st.caption("Add a few tasks. These feed into the scheduler.")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
with col4:
    preferred_time = st.selectbox("Time of day", ["morning", "afternoon", "evening", "any"])
with col5:
    task_time = st.text_input("Scheduled time", value="08:00")

if st.button("Add task"):
    new_task = Task(
        name=task_title,
        category="general",
        duration=int(duration),
        priority=priority,
        preferred_time=preferred_time,
        pet_name=st.session_state.pet.name,
        time=task_time,
    )
    prospective = st.session_state.pet.tasks + [new_task]
    conflicts = st.session_state.scheduler.detect_conflicts(prospective)
    new_task_conflicts = [c for c in conflicts if new_task.name in c]
    if new_task_conflicts:
        for conflict in new_task_conflicts:
            st.warning(f"Scheduling conflict detected — {conflict.replace('WARNING: ', '')}. Task was not added.")
    else:
        st.session_state.pet.add_task(new_task)
        st.session_state.schedule_stale = True
        st.success(f"Added: {new_task.name} at {task_time} ({priority} priority, {duration} min)")

current_tasks = st.session_state.pet.tasks
if current_tasks:
    scheduler = st.session_state.scheduler

    # Filter controls
    filter_col1, filter_col2 = st.columns([1, 3])
    with filter_col1:
        show_filter = st.selectbox("Show", ["All", "Incomplete", "Completed"])

    completed_filter = {"All": None, "Incomplete": False, "Completed": True}[show_filter]
    filtered = scheduler.filter_tasks(current_tasks, completed=completed_filter)
    sorted_tasks = scheduler.sort_by_time(filtered)

    if sorted_tasks:
        st.caption(f"Showing {len(sorted_tasks)} of {len(current_tasks)} task(s) · sorted by scheduled time · edit duration/priority inline · check to complete · 🗑 to delete")
        rows = [
            {
                "_idx": current_tasks.index(t),
                "Scheduled Time": t.time,
                "Task": t.name,
                "Duration (min)": t.duration,
                "Priority": t.priority,
                "Time of Day": t.preferred_time,
                "Completed": t.completed,
            }
            for t in sorted_tasks
        ]
        edited = st.data_editor(
            rows,
            column_config={
                "_idx": None,
                "Completed": st.column_config.CheckboxColumn("Completed"),
                "Duration (min)": st.column_config.NumberColumn("Duration (min)", min_value=1, max_value=240, step=1),
                "Priority": st.column_config.SelectboxColumn("Priority", options=["low", "medium", "high"]),
            },
            disabled=["Scheduled Time", "Task", "Time of Day"],
            hide_index=True,
            num_rows="dynamic",
            use_container_width=True,
        )

        # Sync edits and deletions back to pet.tasks
        edited_indices = {row["_idx"] for row in edited}
        deleted_indices = {row["_idx"] for row in rows} - edited_indices
        changed = False

        if deleted_indices:
            st.session_state.pet.tasks = [
                t for i, t in enumerate(current_tasks) if i not in deleted_indices
            ]
            changed = True

        for row in edited:
            task = current_tasks[row["_idx"]]
            new_duration = int(row["Duration (min)"] or task.duration)
            new_priority = row["Priority"] or task.priority
            if task.duration != new_duration or task.priority != new_priority or task.completed != row["Completed"]:
                task.duration = new_duration
                task.priority = new_priority
                task.completed = row["Completed"]
                changed = True

        if changed:
            st.session_state.schedule_stale = True
    else:
        st.info("No tasks match the selected filter.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()

st.subheader("Build Schedule")
st.caption("Sorts tasks by priority and preferred time, fitting them within your available time budget.")
if st.session_state.schedule_stale:
    st.info("Your tasks have changed. Regenerate the schedule to get the latest version.")

if st.button("Generate schedule"):
    if not st.session_state.pet.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = st.session_state.scheduler
        schedule = scheduler.generate_schedule()
        st.session_state.schedule_stale = False

        # Summary banner
        time_budget = st.session_state.owner.time_available
        time_used = schedule.total_duration
        time_left = time_budget - time_used
        st.success(
            f"Schedule built for {st.session_state.pet.name}! "
            f"{time_used} min scheduled out of {time_budget} min available "
            f"({time_left} min free)."
        )

        # Conflict check on scheduled tasks
        conflicts = scheduler.detect_conflicts(schedule.tasks)
        for conflict in conflicts:
            st.warning(
                f"Conflict in schedule — {conflict.replace('WARNING: ', '')}. "
                "Consider adjusting the scheduled times for these tasks."
            )

        # Scheduled tasks table
        st.markdown("#### Scheduled Tasks (sorted by priority)")
        st.table(schedule.to_dict_list())

        # Per-task reasoning
        st.markdown("#### Why each task was chosen")
        reasoning = schedule.get_reasoning()
        for task_name, reason in reasoning.items():
            if reason.startswith("Included"):
                st.success(f"**{task_name}** — {reason}")
            else:
                st.warning(f"**{task_name}** — {reason}")
