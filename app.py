import os
import streamlit as st
from petnest_system import Task, Pet, Owner, Scheduler
from ai_advisor import AIAdvisor

st.set_page_config(page_title="PetNest", page_icon="🐾", layout="centered")

# --- Sidebar: API key ---
with st.sidebar:
    st.header("AI Settings")
    api_key_input = st.text_input(
        "Google API Key",
        type="password",
        value=os.environ.get("GOOGLE_API_KEY", ""),
        help="Free key from aistudio.google.com. Required for AI suggestions and plan explanations.",
    )
    st.caption("Get a free key at aistudio.google.com → Get API key.")
    st.caption("Your key is never stored or logged.")

st.title("🐾 PetNest")

# --- Session state init ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", time_available=120, preferences={"prefer_morning": True})
if "scheduler" not in st.session_state:
    st.session_state.scheduler = Scheduler(st.session_state.owner)
if "schedule_stale" not in st.session_state:
    st.session_state.schedule_stale = False
if "ai_suggestions" not in st.session_state:
    st.session_state.ai_suggestions = []
if "last_schedule" not in st.session_state:
    st.session_state.last_schedule = None
if "ai_explanation" not in st.session_state:
    st.session_state.ai_explanation = None

# --- Owner & Pet profile ---
st.subheader("Owner & Pet Profile")
col_o1, col_o2 = st.columns(2)
with col_o1:
    owner_name = st.text_input("Owner name", value="Jordan")
with col_o2:
    time_available = st.number_input(
        "Available time (min) today", min_value=10, max_value=480, value=120, step=10
    )

col_p1, col_p2, col_p3 = st.columns(3)
with col_p1:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_p2:
    species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
with col_p3:
    age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

health_notes = st.text_input(
    "Health notes (optional)",
    placeholder="e.g. diabetic, hip dysplasia, senior diet",
)

st.session_state.owner.name = owner_name
st.session_state.owner.time_available = time_available

# --- AI Suggestions (Step 1 of agentic loop: Gemini suggests tasks) ---
st.divider()
st.subheader("AI-Suggested Tasks")
st.caption(
    "Gemini analyses your pet's profile and suggests appropriate care tasks for today. "
    "Review and add the ones you want."
)

if st.button("Get AI Suggestions", type="primary"):
    if not api_key_input:
        st.warning("Enter your Gemini API key in the sidebar to use AI suggestions.")
    else:
        with st.spinner(f"Asking Gemini to suggest tasks for {pet_name}..."):
            pet = next(
                (p for p in st.session_state.owner.pets if p.name == pet_name), None
            )
            if pet is None:
                pet = Pet(pet_name, species, age=age, health_notes=health_notes)
                st.session_state.owner.add_pet(pet)
            else:
                pet.species = species
                pet.age = age
                pet.health_notes = health_notes

            try:
                advisor = AIAdvisor(api_key=api_key_input)
                suggestions = advisor.suggest_tasks(pet, time_available)
                st.session_state.ai_suggestions = suggestions
                st.session_state.ai_explanation = None
                if not suggestions:
                    st.error(
                        "Gemini returned no suggestions. "
                        "Check petnest_advisor.log for details."
                    )
            except Exception as e:
                st.error(f"AI suggestion failed: {e}")

if st.session_state.ai_suggestions:
    st.markdown(
        f"**AI suggested {len(st.session_state.ai_suggestions)} tasks.** "
        "Select which to add:"
    )
    for i, s in enumerate(st.session_state.ai_suggestions):
        col_check, col_info = st.columns([1, 9])
        with col_check:
            st.checkbox(
                f"Select suggestion {i + 1}",
                key=f"sug_{i}",
                value=True,
                label_visibility="collapsed",
            )
        with col_info:
            st.markdown(
                f"**{s['name']}** · {s['category']} · {s['duration']} min · "
                f"{s['priority']} priority · {s['preferred_time']} ({s.get('time', '09:00')})"
            )
            st.caption(s.get("reason", ""))

    if st.button("Add selected suggestions"):
        pet = next(
            (p for p in st.session_state.owner.pets if p.name == pet_name), None
        )
        if pet is None:
            pet = Pet(pet_name, species, age=age, health_notes=health_notes)
            st.session_state.owner.add_pet(pet)

        selected = [
            s
            for i, s in enumerate(st.session_state.ai_suggestions)
            if st.session_state.get(f"sug_{i}", True)
        ]
        for s in selected:
            pet.add_task(
                Task(
                    name=s["name"],
                    category=s.get("category", "other"),
                    duration=int(s["duration"]),
                    priority=s.get("priority", "medium"),
                    preferred_time=s.get("preferred_time", "any"),
                    pet_name=pet_name,
                    time=s.get("time", "09:00"),
                )
            )
        st.session_state.ai_suggestions = []
        st.session_state.schedule_stale = True
        st.success(f"Added {len(selected)} AI-suggested task(s).")
        st.rerun()

# --- Manual task input ---
st.divider()
st.subheader("Tasks")
st.caption("Add tasks manually, or use AI Suggestions above.")

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
    existing_pet = next(
        (p for p in st.session_state.owner.pets if p.name == pet_name), None
    )
    if existing_pet is None:
        existing_pet = Pet(pet_name, species, age=age, health_notes=health_notes)
        st.session_state.owner.add_pet(existing_pet)
    else:
        existing_pet.age = age
        existing_pet.health_notes = health_notes

    new_task = Task(
        name=task_title,
        category="general",
        duration=int(duration),
        priority=priority,
        preferred_time=preferred_time,
        pet_name=pet_name,
        time=task_time,
    )
    prospective = st.session_state.owner.tasks + [new_task]
    conflicts = st.session_state.scheduler.detect_conflicts(prospective)
    new_task_conflicts = [c for c in conflicts if new_task.name in c]
    if new_task_conflicts:
        for conflict in new_task_conflicts:
            st.warning(
                f"Scheduling conflict detected — {conflict.replace('WARNING: ', '')}. "
                "Task was not added."
            )
    else:
        existing_pet.add_task(new_task)
        st.session_state.schedule_stale = True
        st.success(
            f"Added: {new_task.name} at {task_time} ({priority} priority, {duration} min)"
        )

current_tasks = st.session_state.owner.tasks
if current_tasks:
    scheduler = st.session_state.scheduler

    filter_col1, _ = st.columns([1, 3])
    with filter_col1:
        show_filter = st.selectbox("Show", ["All", "Incomplete", "Completed"])

    completed_filter = {"All": None, "Incomplete": False, "Completed": True}[show_filter]
    filtered = scheduler.filter_tasks(current_tasks, completed=completed_filter)
    sorted_tasks = scheduler.sort_by_time(filtered)

    if sorted_tasks:
        st.caption(
            f"Showing {len(sorted_tasks)} of {len(current_tasks)} task(s) · "
            "sorted by scheduled time · edit duration/priority inline · "
            "check to complete · 🗑 to delete"
        )
        task_by_id = {id(t): t for t in sorted_tasks}
        rows = [
            {
                "_id": id(t),
                "Scheduled Time": t.time,
                "Pet": t.pet_name,
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
                "_id": None,
                "Completed": st.column_config.CheckboxColumn("Completed"),
                "Duration (min)": st.column_config.NumberColumn(
                    "Duration (min)", min_value=1, max_value=240, step=1
                ),
                "Priority": st.column_config.SelectboxColumn(
                    "Priority", options=["low", "medium", "high"]
                ),
            },
            disabled=["Scheduled Time", "Pet", "Task", "Time of Day"],
            hide_index=True,
            num_rows="dynamic",
            width="stretch",
        )

        edited_ids = {row["_id"] for row in edited}
        deleted_ids = set(task_by_id.keys()) - edited_ids
        changed = False

        if deleted_ids:
            for tid in deleted_ids:
                task = task_by_id[tid]
                for pet in st.session_state.owner.pets:
                    pet.remove_task(task.name)
            changed = True

        for row in edited:
            task = task_by_id.get(row["_id"])
            if task is None:
                continue
            new_duration = int(row["Duration (min)"] or task.duration)
            new_priority = row["Priority"] or task.priority
            if (
                task.duration != new_duration
                or task.priority != new_priority
                or task.completed != row["Completed"]
            ):
                task.duration = new_duration
                task.priority = new_priority
                task.completed = row["Completed"]
                changed = True

        if changed:
            st.session_state.schedule_stale = True
    else:
        st.info("No tasks match the selected filter.")
else:
    st.info("No tasks yet. Add tasks manually or use AI Suggestions above.")

# --- Build Schedule (Step 2: scheduler validates & fits tasks) ---
st.divider()
st.subheader("Build Schedule")
st.caption(
    "Sorts tasks by priority and preferred time, fitting them within your available time budget."
)
if st.session_state.schedule_stale:
    st.info("Your tasks have changed. Regenerate the schedule to get the latest version.")

if st.button("Generate schedule"):
    if not st.session_state.owner.tasks:
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = st.session_state.scheduler
        schedule = scheduler.generate_schedule()
        st.session_state.last_schedule = schedule
        st.session_state.schedule_stale = False
        st.session_state.ai_explanation = None

pet_names_display = ", ".join(p.name for p in st.session_state.owner.pets)
if st.session_state.last_schedule and not st.session_state.schedule_stale:
    schedule = st.session_state.last_schedule
    scheduler = st.session_state.scheduler
    time_budget = st.session_state.owner.time_available
    time_used = schedule.total_duration

    st.success(
        f"Schedule built for {pet_names_display}! "
        f"{time_used} min scheduled out of {time_budget} min available "
        f"({time_budget - time_used} min free)."
    )

    conflicts = scheduler.detect_conflicts(schedule.tasks)
    for conflict in conflicts:
        st.warning(
            f"Conflict in schedule — {conflict.replace('WARNING: ', '')}. "
            "Consider adjusting the scheduled times for these tasks."
        )

    st.markdown("#### Scheduled Tasks (sorted by priority)")
    st.table(schedule.to_dict_list())

    st.markdown("#### Why each task was chosen")
    for task_name, reason in schedule.get_reasoning().items():
        if reason.startswith("Included"):
            st.success(f"**{task_name}** — {reason}")
        else:
            st.warning(f"**{task_name}** — {reason}")

    # --- AI Plan Explanation (Step 3: Gemini explains the final schedule) ---
    st.divider()
    st.subheader("AI Plan Explanation")
    st.caption(
        "AI will explain why today's schedule is the right plan for your pet(s), "
        "in plain English."
    )

    if st.button("Explain plan with AI"):
        if not api_key_input:
            st.warning("Enter your Gemini API key in the sidebar.")
        else:
            with st.spinner("Generating explanation..."):
                try:
                    advisor = AIAdvisor(api_key=api_key_input)
                    explanation = advisor.explain_schedule(
                        schedule, st.session_state.owner
                    )
                    st.session_state.ai_explanation = explanation
                except Exception as e:
                    st.error(f"AI explanation failed: {e}")

    if st.session_state.ai_explanation:
        st.info(st.session_state.ai_explanation)
