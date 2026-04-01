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

# --- Owner Setup ---
st.subheader("Owner Info")
col_name, col_time = st.columns(2)
with col_name:
    owner_name = st.text_input("Owner name", value=st.session_state.owner.name)
with col_time:
    available_minutes = st.number_input(
        "Available minutes today", min_value=1, max_value=480,
        value=st.session_state.owner.available_minutes,
    )

# Keep owner in sync with inputs
st.session_state.owner.name = owner_name
st.session_state.owner.available_minutes = available_minutes

st.divider()

# --- Add a Pet ---
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

# Show current pets
if st.session_state.owner.pets:
    st.write("**Your pets:**")
    for pet in st.session_state.owner.pets:
        st.write(f"- {pet.summary()} — {len(pet.tasks)} task(s)")
else:
    st.info("No pets yet. Add one above.")

st.divider()

# --- Add a Task to a Pet ---
st.subheader("Add a Task")

if st.session_state.owner.pets:
    pet_names = [p.name for p in st.session_state.owner.pets]
    selected_pet_name = st.selectbox("Assign to pet", pet_names)

    col1, col2 = st.columns(2)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox("Category", ["walk", "feeding", "medication", "grooming", "enrichment"])
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        priority = st.selectbox("Priority", ["high", "medium", "low"])

    if st.button("Add task"):
        selected_pet = next(p for p in st.session_state.owner.pets if p.name == selected_pet_name)
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
        )
        selected_pet.add_task(new_task)
        st.success(f"Added '{task_title}' to {selected_pet_name}'s tasks!")

    # Show all tasks across pets
    all_tasks = st.session_state.owner.all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        task_data = [
            {
                "Pet": next(p.name for p in st.session_state.owner.pets if t in p.tasks),
                "Task": t.title,
                "Duration": f"{t.duration_minutes}min",
                "Priority": t.priority,
                "Category": t.category,
            }
            for t in all_tasks
        ]
        st.table(task_data)
else:
    st.info("Add a pet first, then you can assign tasks to it.")

st.divider()

# --- Generate Schedule ---
st.subheader("Generate Daily Schedule")

if st.button("Generate schedule"):
    if not st.session_state.owner.all_pending_tasks():
        st.warning("No pending tasks to schedule. Add some tasks first!")
    else:
        scheduler = Scheduler(st.session_state.owner)
        scheduler.generate_schedule()
        st.code(scheduler.explain_plan())
