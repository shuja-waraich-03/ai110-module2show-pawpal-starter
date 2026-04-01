from dataclasses import dataclass, field

PRIORITY_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    """Represents a single pet care activity."""

    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    category: str  # walk, feeding, medication, grooming, enrichment
    frequency: str = "daily"  # daily, weekly, as-needed
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True if this task's priority is 'high'."""
        return self.priority == "high"

    def mark_complete(self) -> None:
        """Set the task's completed status to True."""
        self.completed = True

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

    def _sort_by_priority(self, tasks: list[tuple[Task, str]]) -> list[tuple[Task, str]]:
        """Sort task-pet pairs by descending priority rank."""
        return sorted(tasks, key=lambda pair: PRIORITY_RANK.get(pair[0].priority, 0), reverse=True)

    def generate_schedule(self) -> list[ScheduledTask]:
        """Build a daily schedule by greedily fitting highest-priority tasks first."""
        self.scheduled_tasks = []
        current_minute = 0
        remaining = self.owner.available_minutes

        # Gather all pending tasks paired with pet name
        task_pet_pairs: list[tuple[Task, str]] = []
        for pet in self.owner.pets:
            for task in pet.pending_tasks():
                task_pet_pairs.append((task, pet.name))

        # Sort by priority (high first), then by duration (shorter first for ties)
        sorted_pairs = sorted(
            task_pet_pairs,
            key=lambda pair: (-PRIORITY_RANK.get(pair[0].priority, 0), pair[0].duration_minutes),
        )

        for task, pet_name in sorted_pairs:
            if task.duration_minutes <= remaining:
                self.scheduled_tasks.append(
                    ScheduledTask(task=task, start_minute=current_minute, pet_name=pet_name)
                )
                current_minute += task.duration_minutes
                remaining -= task.duration_minutes

        return self.scheduled_tasks

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
            lines.append(
                f"  {i}. [{st.time_label()}] {st.task.title} "
                f"for {st.pet_name} — {st.task.duration_minutes}min ({reason})"
            )
            total_used += st.task.duration_minutes

        skipped = [
            t for t in self.owner.all_pending_tasks()
            if t not in [s.task for s in self.scheduled_tasks]
        ]

        lines.append(f"\nTotal scheduled: {total_used} of {self.owner.available_minutes} minutes.")

        if skipped:
            lines.append(f"Skipped {len(skipped)} task(s) that didn't fit:")
            for t in skipped:
                lines.append(f"  - {t.title} ({t.duration_minutes}min, {t.priority})")

        return "\n".join(lines)
