from datetime import date, timedelta

from pawpal_system import Owner, Pet, Scheduler, Task


# ── Existing tests ──────────────────────────────────────────────────


def test_mark_complete_changes_status():
    task = Task("Morning walk", 30, "high", "walk")
    assert task.completed is False

    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Mochi", "dog", 3)
    assert len(pet.tasks) == 0

    pet.add_task(Task("Feed breakfast", 10, "high", "feeding"))
    assert len(pet.tasks) == 1

    pet.add_task(Task("Brush fur", 15, "medium", "grooming"))
    assert len(pet.tasks) == 2


# ── Sorting Correctness ────────────────────────────────────────────


def test_sort_by_time_returns_chronological_order():
    """Tasks are returned earliest preferred_time first."""
    t1 = Task("Evening walk", 30, "low", "walk", preferred_time="18:00")
    t2 = Task("Morning meds", 5, "high", "medication", preferred_time="07:30")
    t3 = Task("Lunch feed", 10, "medium", "feeding", preferred_time="12:00")

    sorted_tasks = Scheduler.sort_by_time([t1, t2, t3])

    assert [t.title for t in sorted_tasks] == [
        "Morning meds",
        "Lunch feed",
        "Evening walk",
    ]


def test_sort_by_time_places_empty_time_last():
    """Tasks without a preferred_time sort after all timed tasks."""
    t1 = Task("No time task", 10, "high", "walk", preferred_time="")
    t2 = Task("Early task", 10, "high", "walk", preferred_time="06:00")

    sorted_tasks = Scheduler.sort_by_time([t1, t2])

    assert sorted_tasks[0].title == "Early task"
    assert sorted_tasks[1].title == "No time task"


def test_generate_schedule_priority_sorts_high_first():
    """Default priority sort puts high-priority tasks before low."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Low task", 10, "low", "walk"),
        Task("High task", 10, "high", "feeding"),
    ])
    owner = Owner("Alice", 60, pets=[pet])
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule(sort_by="priority")

    assert schedule[0].task.title == "High task"
    assert schedule[1].task.title == "Low task"


def test_generate_schedule_shortest_first():
    """shortest_first sort orders by ascending duration."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Long walk", 60, "high", "walk"),
        Task("Quick feed", 5, "high", "feeding"),
        Task("Medium groom", 20, "high", "grooming"),
    ])
    owner = Owner("Alice", 120, pets=[pet])
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule(sort_by="shortest_first")

    durations = [st.task.duration_minutes for st in schedule]
    assert durations == [5, 20, 60]


# ── Recurrence Logic ───────────────────────────────────────────────


def test_daily_task_creates_next_day_occurrence():
    """Completing a daily task returns a new task due tomorrow."""
    today = date.today()
    task = Task("Morning walk", 30, "high", "walk", frequency="daily", due_date=today)

    next_task = task.mark_complete()

    assert task.completed is True
    assert next_task is not None
    assert next_task.due_date == today + timedelta(days=1)
    assert next_task.completed is False
    assert next_task.title == "Morning walk"


def test_weekly_task_creates_next_week_occurrence():
    """Completing a weekly task returns a new task due in 7 days."""
    today = date.today()
    task = Task("Bath time", 45, "medium", "grooming", frequency="weekly", due_date=today)

    next_task = task.mark_complete()

    assert next_task is not None
    assert next_task.due_date == today + timedelta(weeks=1)


def test_as_needed_task_does_not_recur():
    """Completing an as-needed task returns None (no next occurrence)."""
    task = Task("Nail trim", 20, "low", "grooming", frequency="as-needed")

    next_task = task.mark_complete()

    assert next_task is None


def test_pet_complete_task_appends_next_occurrence():
    """Pet.complete_task auto-adds the recurring next task to pet.tasks."""
    pet = Pet("Mochi", "dog", 3)
    pet.add_task(Task("Morning walk", 30, "high", "walk", frequency="daily"))

    pet.complete_task("Morning walk")

    assert len(pet.tasks) == 2
    assert pet.tasks[0].completed is True
    assert pet.tasks[1].completed is False
    assert pet.tasks[1].due_date == date.today() + timedelta(days=1)


# ── Conflict Detection ─────────────────────────────────────────────


def test_same_time_conflict_detected_same_pet():
    """Two tasks at the same preferred_time for one pet trigger a warning."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Walk", 30, "high", "walk", preferred_time="08:00"),
        Task("Feed", 10, "high", "feeding", preferred_time="08:00"),
    ])
    owner = Owner("Alice", 120, pets=[pet])
    scheduler = Scheduler(owner)

    scheduler.generate_schedule(sort_by="time")

    assert len(scheduler.conflicts) >= 1
    assert any("08:00" in c for c in scheduler.conflicts)
    assert any("Mochi" in c for c in scheduler.conflicts)


def test_same_time_conflict_detected_different_pets():
    """Same preferred_time across two pets warns owner can't be in two places."""
    pet1 = Pet("Mochi", "dog", 3, tasks=[
        Task("Walk Mochi", 30, "high", "walk", preferred_time="09:00"),
    ])
    pet2 = Pet("Whiskers", "cat", 5, tasks=[
        Task("Feed Whiskers", 10, "high", "feeding", preferred_time="09:00"),
    ])
    owner = Owner("Alice", 120, pets=[pet1, pet2])
    scheduler = Scheduler(owner)

    scheduler.generate_schedule(sort_by="time")

    assert len(scheduler.conflicts) >= 1
    assert any("owner can only be in one place" in c for c in scheduler.conflicts)


def test_back_to_back_same_category_conflict():
    """Consecutive same-category tasks for one pet trigger a warning."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Short walk", 15, "high", "walk", preferred_time="08:00"),
        Task("Long walk", 30, "medium", "walk", preferred_time="08:30"),
    ])
    owner = Owner("Alice", 120, pets=[pet])
    scheduler = Scheduler(owner)

    scheduler.generate_schedule(sort_by="time")

    assert any("back-to-back" in c for c in scheduler.conflicts)


# ── Time Budget / Overflow ──────────────────────────────────────────


def test_tasks_exceeding_budget_are_skipped():
    """Tasks that don't fit in available_minutes are left out of the schedule."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Long walk", 50, "high", "walk"),
        Task("Quick feed", 10, "medium", "feeding"),
        Task("Grooming", 45, "low", "grooming"),
    ])
    owner = Owner("Alice", 60, pets=[pet])
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule(sort_by="priority")

    total_scheduled = sum(st.task.duration_minutes for st in schedule)
    assert total_scheduled <= 60
    assert len(schedule) == 2  # Long walk (50) + Quick feed (10) = 60


def test_zero_available_minutes_produces_empty_schedule():
    """Owner with zero minutes gets no scheduled tasks."""
    pet = Pet("Mochi", "dog", 3, tasks=[
        Task("Walk", 30, "high", "walk"),
    ])
    owner = Owner("Alice", 0, pets=[pet])
    scheduler = Scheduler(owner)

    schedule = scheduler.generate_schedule()

    assert schedule == []
