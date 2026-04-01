```mermaid
classDiagram
    class Owner {
        +String name
        +int available_minutes
        +List~String~ preferences
        +has_time_for(task) bool
    }

    class Pet {
        +String name
        +String species
        +int age
        +summary() String
    }

    class Task {
        +String title
        +int duration_minutes
        +String priority
        +String category
        +is_high_priority() bool
        +__repr__() String
    }

    class ScheduledTask {
        +Task task
        +int start_minute
        +time_label() String
    }

    class Scheduler {
        +Owner owner
        +Pet pet
        +List~Task~ tasks
        +List~ScheduledTask~ scheduled_tasks
        +generate_schedule() List~ScheduledTask~
        +explain_plan() String
    }

    Owner "1" --> "1" Pet : owns
    Pet "1" --> "*" Task : has
    ScheduledTask --> Task : wraps
    Scheduler --> Owner : uses
    Scheduler --> Pet : uses
    Scheduler --> ScheduledTask : produces
```
