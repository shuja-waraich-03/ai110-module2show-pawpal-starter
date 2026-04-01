from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# --- Create owner ---
owner = Owner(name="Jordan", available_minutes=120, preferences=["prefer morning walks"])

# --- Create pets ---
mochi = Pet(name="Mochi", species="dog", age=3)
whiskers = Pet(name="Whiskers", species="cat", age=5)

owner.add_pet(mochi)
owner.add_pet(whiskers)

# --- Add tasks with INTENTIONAL CONFLICTS ---

# Conflict 1: Same pet, same preferred_time
mochi.add_task(Task("Morning walk", 30, "high", "walk", preferred_time="07:30"))
mochi.add_task(Task("Feed breakfast", 10, "high", "feeding", preferred_time="07:30"))  # same time!

# Conflict 2: Different pets, same preferred_time (owner can't do both at once)
whiskers.add_task(Task("Give medication", 5, "high", "medication", preferred_time="08:00"))
mochi.add_task(Task("Obedience training", 20, "medium", "enrichment", preferred_time="08:00"))  # same time!

# Conflict 3: Back-to-back same category for same pet
mochi.add_task(Task("Evening walk", 25, "medium", "walk", preferred_time="18:00"))
# Morning walk + Evening walk are both "walk" category for Mochi

# Normal tasks (no conflicts)
whiskers.add_task(Task("Brush fur", 15, "medium", "grooming", preferred_time="17:00"))
whiskers.add_task(Task("Interactive toy time", 20, "low", "enrichment", preferred_time="10:00"))

# =============================================
print("=" * 60)
print("SCHEDULE SORTED BY TIME (with conflict detection)")
print("=" * 60)
scheduler = Scheduler(owner)
scheduler.generate_schedule(sort_by="time")
print(scheduler.explain_plan())

# =============================================
print("\n" + "=" * 60)
print("ALL DETECTED CONFLICTS")
print("=" * 60)
if scheduler.conflicts:
    for i, c in enumerate(scheduler.conflicts, 1):
        print(f"  {i}. {c}")
else:
    print("  No conflicts detected.")

# =============================================
print("\n" + "=" * 60)
print("SCHEDULE SORTED BY PRIORITY (with conflict detection)")
print("=" * 60)
scheduler2 = Scheduler(owner)
scheduler2.generate_schedule(sort_by="priority")
print(scheduler2.explain_plan())

# =============================================
# Show that conflict-free schedules report clean
print("\n" + "=" * 60)
print("CONFLICT-FREE SCHEDULE (clean setup)")
print("=" * 60)
owner2 = Owner(name="Alex", available_minutes=60)
buddy = Pet(name="Buddy", species="dog", age=2)
owner2.add_pet(buddy)
buddy.add_task(Task("Walk", 20, "high", "walk", preferred_time="07:00"))
buddy.add_task(Task("Feed", 10, "high", "feeding", preferred_time="08:00"))
buddy.add_task(Task("Grooming", 15, "medium", "grooming", preferred_time="09:00"))

scheduler3 = Scheduler(owner2)
scheduler3.generate_schedule(sort_by="time")
print(scheduler3.explain_plan())
if not scheduler3.conflicts:
    print("\n  All clear — no conflicts detected!")
