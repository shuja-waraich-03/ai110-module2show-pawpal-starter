import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    "A pet care planning assistant that helps you organize daily tasks "
    "for your pets based on priority and available time."
)

# --- Initialize session state ---
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=90)

st.divider()

# ─── Owner Setup ────────────────────────────────────────────────────

st.subheader("Owner Info")
col_name, col_time = st.columns(2)
with col_name:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
with col_time:
    available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=480,
        value=st.session_state.owner.available_minutes,
    )

st.session_state.owner.name = owner_name
st.session_state.owner.available_minutes = available_minutes

st.divider()

# ─── Add a Pet ──────────────────────────────────────────────────────

st.subheader("Add a Pet")
col_pet, col_species, col_age = st.columns(3)
with col_pet:
    pet_name = st.text_input("Pet name", value="Mochi")
with col_species:
    species = st.selectbox("Species", ["dog", "cat", "other"])
with col_age:
    pet_age = st.number_input("Age (years)", min_value=0, max_value=30, value=3)

if st.button("Add pet"):
    new_pet = Pet(name=pet_name, species=species, age=pet_age)
    st.session_state.owner.add_pet(new_pet)
    st.success(f"Added {new_pet.summary()} to {st.session_state.owner.name}'s pets!")

if st.session_state.owner.pets:
    st.write("**Your pets:**")
    for pet in st.session_state.owner.pets:
        st.write(f"- {pet.summary()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# ─── Add a Task ─────────────────────────────────────────────────────

st.subheader("Add a Task")

if st.session_state.owner.pets:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign to pet", pet_names)

    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox(
            "Category", ["walk", "feeding", "medication", "grooming", "enrichment"],
        )
        frequency = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
    with col2:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20,
        )
        priority = st.selectbox("Priority", ["high", "medium", "low"])
        preferred_time = st.text_input(
            "Preferred time (HH:MM)", value="", placeholder="e.g. 08:00",
        )

    if st.button("Add task"):
        selected_pet = next(
            p for p in st.session_state.owner.pets if p.name == selected_pet_name
        )
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            preferred_time=preferred_time,
            frequency=frequency,
        )
        selected_pet.add_task(new_task)
        st.success(f"Added '{task_title}' to {selected_pet_name}'s tasks!")

    # ─── Task Table with Filters ────────────────────────────────────

    all_tasks = st.session_state.owner.all_tasks()
    if all_tasks:
        st.markdown("---")
        st.subheader("All Tasks")

        # Filter controls
        filter_col1, filter_col2, filter_col3 = st.columns(3)
        with filter_col1:
            filter_status = st.selectbox(
                "Filter by status", ["all", "pending", "completed"],
            )
        with filter_col2:
            filter_pet = st.selectbox(
                "Filter by pet", ["all"] + pet_names,
            )
        with filter_col3:
            filter_category = st.selectbox(
                "Filter by category",
                ["all", "walk", "feeding", "medication", "grooming", "enrichment"],
            )

        filtered = Scheduler.filter_tasks(
            all_tasks,
            status=filter_status if filter_status != "all" else None,
            pet_name=filter_pet if filter_pet != "all" else None,
            category=filter_category if filter_category != "all" else None,
            pets_lookup=st.session_state.owner.pets,
        )

        if filtered:
            task_data = []
            for t in filtered:
                pet_label = next(
                    (p.name for p in st.session_state.owner.pets if t in p.tasks), "?"
                )
                task_data.append({
                    "Pet": pet_label,
                    "Task": t.title,
                    "Duration": f"{t.duration_minutes}min",
                    "Priority": t.priority,
                    "Category": t.category,
                    "Time": t.preferred_time or "—",
                    "Frequency": t.frequency,
                    "Status": "✅ Done" if t.completed else "⏳ Pending",
                })
            st.table(task_data)
        else:
            st.info("No tasks match the current filters.")

    # ─── Mark a Task Complete ───────────────────────────────────────

    pending = st.session_state.owner.all_pending_tasks()
    if pending:
        st.markdown("---")
        st.subheader("Complete a Task")
        pending_labels = [
            f"{t.title} ({next(p.name for p in st.session_state.owner.pets if t in p.tasks)})"
            for t in pending
        ]
        selected_complete = st.selectbox("Select task to complete", pending_labels)

        if st.button("Mark complete"):
            idx = pending_labels.index(selected_complete)
            task_to_complete = pending[idx]
            pet_for_task = next(
                p for p in st.session_state.owner.pets if task_to_complete in p.tasks
            )
            next_task = pet_for_task.complete_task(task_to_complete.title)
            st.success(f"'{task_to_complete.title}' marked complete!")
            if next_task:
                st.info(
                    f"Recurring task: next '{next_task.title}' created for "
                    f"{next_task.due_date}."
                )
            st.rerun()

else:
    st.info("Add a pet first, then you can assign tasks to it.")

st.divider()

# ─── Generate Schedule ──────────────────────────────────────────────

st.subheader("Generate Daily Schedule")

sort_option = st.selectbox(
    "Sort strategy",
    ["priority", "time", "shortest_first", "longest_first"],
    help=(
        "priority — high priority first, then shortest duration | "
        "time — by preferred time (HH:MM) | "
        "shortest_first / longest_first — by duration"
    ),
)

if st.button("Generate schedule"):
    if not st.session_state.owner.all_pending_tasks():
        st.warning("No pending tasks to schedule. Add some tasks first!")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.generate_schedule(sort_by=sort_option)

        # ── Scheduled tasks table ───────────────────────────────────
        if scheduler.scheduled_tasks:
            st.success(
                f"Scheduled {len(scheduler.scheduled_tasks)} task(s) "
                f"for {st.session_state.owner.name}."
            )
            schedule_data = []
            for i, st_item in enumerate(scheduler.scheduled_tasks, start=1):
                schedule_data.append({
                    "#": i,
                    "Time offset": st_item.time_label(),
                    "Task": st_item.task.title,
                    "Pet": st_item.pet_name,
                    "Duration": f"{st_item.task.duration_minutes}min",
                    "Priority": st_item.task.priority,
                    "Category": st_item.task.category,
                    "Preferred": st_item.task.preferred_time or "—",
                })
            st.table(schedule_data)

        # ── Conflict warnings ───────────────────────────────────────
        if scheduler.conflicts:
            st.warning(f"⚠ {len(scheduler.conflicts)} conflict(s) detected:")
            for conflict in scheduler.conflicts:
                st.warning(conflict)

        # ── Skipped tasks ───────────────────────────────────────────
        scheduled_ids = {id(s.task) for s in scheduler.scheduled_tasks}
        skipped = [
            t for t in scheduler.owner.all_tasks_due_today()
            if id(t) not in scheduled_ids
        ]
        if skipped:
            st.info(
                f"{len(skipped)} task(s) skipped (not enough time):"
            )
            for t in skipped:
                st.write(f"  - {t.title} ({t.duration_minutes}min, {t.priority})")

        # ── Summary stats ───────────────────────────────────────────
        total_used = sum(s.task.duration_minutes for s in scheduler.scheduled_tasks)
        remaining = st.session_state.owner.available_minutes - total_used
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Scheduled", f"{total_used} min")
        col_b.metric("Remaining", f"{remaining} min")
        col_c.metric("Tasks", len(scheduler.scheduled_tasks))
