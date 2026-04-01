from dataclasses import dataclass, field
from datetime import date, timedelta

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    category: str  # walk, feeding, medication, grooming, enrichment
    preferred_time: str = ""  # "HH:MM" format, e.g. "07:30", "14:00"
    frequency: str = "daily"  # daily, weekly, as-needed
    weekly_day: int = 0  # 0=Monday .. 6=Sunday, only used when frequency="weekly"
    due_date: date | None = None  # the date this task is due; None means today
    flagged_today: bool = False  # manually flag an as-needed task for today
    completed: bool = False

    def __post_init__(self) -> None:
        """Set due_date to today if not provided."""
        if self.due_date is None:
            self.due_date = date.today()

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        if self.due_date and self.due_date != date.today():
            return False
        if self.frequency == "daily":
            return True
        if self.frequency == "weekly":
            return date.today().weekday() == self.weekly_day
        if self.frequency == "as-needed":
            return self.flagged_today
        return True

    def next_due_date(self) -> date | None:
        """Calculate the next due date based on frequency using timedelta."""
        today = self.due_date or date.today()
        if self.frequency == "daily":
            return today + timedelta(days=1)
        if self.frequency == "weekly":
            return today + timedelta(weeks=1)
        return None  # as-needed tasks don't auto-recur

    def create_next_occurrence(self) -> "Task | None":
        """Create a fresh copy of this task for the next due date."""
        next_date = self.next_due_date()
        if next_date is None:
            return None
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            category=self.category,
            preferred_time=self.preferred_time,
            frequency=self.frequency,
            weekly_day=self.weekly_day,
            due_date=next_date,
        )

    def mark_complete(self) -> "Task | None":
        """Mark this task done and return the next occurrence if recurring."""
        self.completed = True
        return self.create_next_occurrence()

    def mark_incomplete(self) -> None:
        """Reset the task's completed status to False."""
        self.completed = False

    def __repr__(self) -> str:
        status = "done" if self.completed else "pending"
        return (
            f"Task('{self.title}', {self.duration_minutes}min, "
            f"priority='{self.priority}', {status})"
        )


@dataclass
class Pet:
    """Stores pet details and owns a list of tasks."""

    name: str
    species: str
    age: int
    tasks: list[Task] = field(default_factory=list)

    def summary(self) -> str:
        """Return a short description like 'Mochi (dog, 3 years old)'."""
        return f"{self.name} ({self.species}, {self.age} years old)"

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, title: str) -> bool:
        """Remove the first task matching the given title; return True if found."""
        for i, t in enumerate(self.tasks):
            if t.title == title:
                self.tasks.pop(i)
                return True
        return False

    def pending_tasks(self) -> list[Task]:
        """Return all tasks that have not been completed."""
        return [t for t in self.tasks if not t.completed]

    def completed_tasks(self) -> list[Task]:
        """Return all tasks that have been completed."""
        return [t for t in self.tasks if t.completed]

    def complete_task(self, title: str) -> "Task | None":
        """Mark a task complete by title and auto-add its next occurrence if recurring."""
        for task in self.tasks:
            if task.title == title and not task.completed:
                next_task = task.mark_complete()
                if next_task:
                    self.tasks.append(next_task)
                return next_task
        return None

    def tasks_by_category(self, category: str) -> list[Task]:
        """Return all tasks matching a specific category."""
        return [t for t in self.tasks if t.category == category]

    def tasks_due_today(self) -> list[Task]:
        """Return pending tasks that are due today based on frequency."""
        return [t for t in self.pending_tasks() if t.is_due_today()]


@dataclass
class Owner:
    """Manages one or more pets and provides access to all their tasks."""

    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def all_tasks(self) -> list[Task]:
        """Collect and return every task across all pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def all_pending_tasks(self) -> list[Task]:
        """Return all incomplete tasks across all pets."""
        return [t for t in self.all_tasks() if not t.completed]

    def all_tasks_due_today(self) -> list[Task]:
        """Return all pending tasks due today across all pets."""
        tasks = []
        for pet in self.pets:
            tasks.extend(pet.tasks_due_today())
        return tasks

    def tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to a specific pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []

    def has_time_for(self, task: Task) -> bool:
        """Return True if the owner has enough available minutes for the task."""
        return task.duration_minutes <= self.available_minutes


@dataclass
class ScheduledTask:
    """Pairs a Task with its position in the daily plan."""

    task: Task
    start_minute: int
    pet_name: str

    def time_label(self) -> str:
        """Return a human-readable time offset like '1h 05m'."""
        hours = self.start_minute // 60
        minutes = self.start_minute % 60
        return f"{hours}h {minutes:02d}m"


class Scheduler:
    """The brain: retrieves, prioritizes, and schedules tasks across all pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner
        self.scheduled_tasks: list[ScheduledTask] = []
        self.conflicts: list[str] = []

    @staticmethod
    def sort_by_time(tasks: list[Task]) -> list[Task]:
        """Sort tasks by their preferred_time in HH:MM format.

        Tasks without a preferred_time are placed at the end.
        Uses a lambda key that splits "HH:MM" into (hours, minutes) for correct ordering.
        """
        return sorted(
            tasks,
            key=lambda t: tuple(int(x) for x in t.preferred_time.split(":")) if t.preferred_time else (99, 99),
        )

    @staticmethod
    def filter_tasks(
        tasks: list[Task],
        status: str | None = None,
        pet_name: str | None = None,
        category: str | None = None,
        pets_lookup: list[Pet] | None = None,
    ) -> list[Task]:
        """Filter a list of tasks by completion status, pet name, and/or category.

        status: "pending", "completed", or None (no filter)
        pet_name: only include tasks belonging to this pet (requires pets_lookup)
        category: only include tasks matching this category
        """
        result = tasks

        if status == "pending":
            result = [t for t in result if not t.completed]
        elif status == "completed":
            result = [t for t in result if t.completed]

        if pet_name and pets_lookup:
            pet_tasks = set()
            for pet in pets_lookup:
                if pet.name == pet_name:
                    pet_tasks = {id(t) for t in pet.tasks}
                    break
            result = [t for t in result if id(t) in pet_tasks]

        if category:
            result = [t for t in result if t.category == category]

        return result

    def generate_schedule(self, sort_by: str = "priority") -> list[ScheduledTask]:
        """Build a daily schedule from tasks due today.

        sort_by options:
            "priority"          — high priority first, then shortest duration
            "time"              — by preferred_time (HH:MM), earliest first
            "shortest_first"    — shortest tasks first regardless of priority
            "longest_first"     — longest tasks first regardless of priority
        """
        self.scheduled_tasks = []
        self.conflicts = []
        current_minute = 0
        remaining = self.owner.available_minutes

        # Only gather tasks that are due today (respects frequency)
        task_pet_pairs: list[tuple[Task, str]] = []
        for pet in self.owner.pets:
            for task in pet.tasks_due_today():
                task_pet_pairs.append((task, pet.name))

        # Sort based on chosen strategy
        if sort_by == "time":
            sorted_pairs = sorted(
                task_pet_pairs,
                key=lambda p: tuple(int(x) for x in p[0].preferred_time.split(":")) if p[0].preferred_time else (99, 99),
            )
        elif sort_by == "shortest_first":
            sorted_pairs = sorted(task_pet_pairs, key=lambda p: p[0].duration_minutes)
        elif sort_by == "longest_first":
            sorted_pairs = sorted(task_pet_pairs, key=lambda p: -p[0].duration_minutes)
        else:
            sorted_pairs = sorted(
                task_pet_pairs,
                key=lambda p: (-PRIORITY_RANK.get(p[0].priority, 0), p[0].duration_minutes),
            )

        for task, pet_name in sorted_pairs:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append(
                    ScheduledTask(task=task, start_minute=current_minute, pet_name=pet_name)
                )
                current_minute += task.duration_minutes
                remaining -= task.duration_minutes

        # Run conflict detection after scheduling
        self._detect_conflicts()

        return self.scheduled_tasks

    def _detect_conflicts(self) -> None:
        """Detect scheduling conflicts and return warnings instead of crashing.

        Checks for:
        1. Same preferred_time — two tasks want the same HH:MM slot
        2. Back-to-back category — consecutive same-category tasks for one pet
        """
        self.conflicts = []
        scheduled = self.scheduled_tasks

        # Check every unique pair for same preferred_time conflicts
        for i in range(len(scheduled)):
            for j in range(i + 1, len(scheduled)):
                a, b = scheduled[i], scheduled[j]

                if not a.task.preferred_time or not b.task.preferred_time:
                    continue
                if a.task.preferred_time != b.task.preferred_time:
                    continue

                if a.pet_name == b.pet_name:
                    self.conflicts.append(
                        f"Warning: '{a.task.title}' and '{b.task.title}' "
                        f"are both scheduled at {a.task.preferred_time} for {a.pet_name}"
                    )
                else:
                    self.conflicts.append(
                        f"Warning: '{a.task.title}' ({a.pet_name}) and "
                        f"'{b.task.title}' ({b.pet_name}) are both scheduled "
                        f"at {a.task.preferred_time} — owner can only be in one place"
                    )

        # Check consecutive tasks for back-to-back same-category conflicts
        for i in range(len(scheduled) - 1):
            current, nxt = scheduled[i], scheduled[i + 1]
            if current.pet_name == nxt.pet_name and current.task.category == nxt.task.category:
                self.conflicts.append(
                    f"Warning: '{current.task.title}' and '{nxt.task.title}' "
                    f"are back-to-back {current.task.category} tasks for {current.pet_name}"
                )

    def explain_plan(self) -> str:
        """Return a human-readable summary of the scheduled plan with reasoning."""
        if not self.scheduled_tasks:
            return "No tasks scheduled. Try generating a schedule first."

        lines = [
            f"Daily plan for {self.owner.name} "
            f"({self.owner.available_minutes} minutes available):\n"
        ]

        total_used = 0
        for i, st in enumerate(self.scheduled_tasks, start=1):
            reason = "high priority" if st.task.is_high_priority() else f"{st.task.priority} priority"
            freq = f", {st.task.frequency}" if st.task.frequency != "daily" else ""
            lines.append(
                f"  {i}. [{st.time_label()}] {st.task.title} "
                f"for {st.pet_name} — {st.task.duration_minutes}min ({reason}{freq})"
            )
            total_used += st.task.duration_minutes

        # Show conflicts
        if self.conflicts:
            lines.append(f"\n⚠ {len(self.conflicts)} conflict(s) detected:")
            for c in self.conflicts:
                lines.append(f"  - {c}")

        # Show skipped tasks
        scheduled_set = {id(s.task) for s in self.scheduled_tasks}
        skipped = [t for t in self.owner.all_tasks_due_today() if id(t) not in scheduled_set]

        lines.append(f"\nTotal scheduled: {total_used} of {self.owner.available_minutes} minutes.")

        if skipped:
            lines.append(f"Skipped {len(skipped)} task(s) that didn't fit:")
            for t in skipped:
                lines.append(f"  - {t.title} ({t.duration_minutes}min, {t.priority})")

        return "\n".join(lines)
