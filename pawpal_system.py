from dataclasses import dataclass, field


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: list[str] = field(default_factory=list)

    def has_time_for(self, task: "Task") -> bool:
        """Return True if the owner has enough available minutes for the task."""
        pass


@dataclass
class Pet:
    name: str
    species: str
    age: int

    def summary(self) -> str:
        """Return a short description like 'Mochi (dog, 3 years old)'."""
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", or "high"
    category: str  # walk, feeding, medication, grooming, enrichment

    def is_high_priority(self) -> bool:
        """Return True if the task priority is 'high'."""
        pass

    def __repr__(self) -> str:
        return f"Task(title='{self.title}', duration={self.duration_minutes}min, priority='{self.priority}')"


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def generate_schedule(self) -> list[Task]:
        """Sort and select tasks that fit within the owner's available time, prioritizing high-priority tasks first."""
        pass

    def explain_plan(self) -> str:
        """Return a human-readable explanation of the scheduled plan."""
        pass
