from pawpal_system import Owner, Pet, Task, Scheduler

# --- Create owner ---
owner = Owner(name="Jordan", available_minutes=90, preferences=["prefer morning walks"])

# --- Create pets ---
mochi = Pet(name="Mochi", species="dog", age=3)
whiskers = Pet(name="Whiskers", species="cat", age=5)

owner.add_pet(mochi)
owner.add_pet(whiskers)

# --- Add tasks for Mochi (dog) ---
mochi.add_task(Task("Morning walk", 30, "high", "walk"))
mochi.add_task(Task("Feed breakfast", 10, "high", "feeding"))
mochi.add_task(Task("Play fetch", 25, "low", "enrichment"))

# --- Add tasks for Whiskers (cat) ---
whiskers.add_task(Task("Give medication", 5, "high", "medication"))
whiskers.add_task(Task("Brush fur", 15, "medium", "grooming"))
whiskers.add_task(Task("Interactive toy time", 20, "low", "enrichment"))

# --- Generate and print schedule ---
print(f"Owner: {owner.name}")
print(f"Pets: {mochi.summary()}, {whiskers.summary()}")
print(f"Total pending tasks: {len(owner.all_pending_tasks())}")
print("=" * 50)

scheduler = Scheduler(owner)
scheduler.generate_schedule()
print(scheduler.explain_plan())
