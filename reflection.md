# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The initial UML design contains five classes, each with a single clear responsibility:

- **Owner** — Stores the owner's name, total available minutes for pet care, and a list of preferences. Responsible for answering whether there is enough time left for a given task (`has_time_for`).
- **Pet** — Stores the pet's name, species, and age. Responsible for producing a short summary string for display purposes.
- **Task** — Represents a single care activity (walk, feeding, medication, grooming, enrichment) with a title, duration, priority level, and category. Responsible for reporting whether it is high priority.
- **ScheduledTask** — A lightweight wrapper that pairs a Task with its `start_minute` in the daily plan. Responsible for producing a human-readable time label.
- **Scheduler** — The core engine. Takes an Owner, Pet, and list of Tasks, then generates an ordered daily schedule that fits within the owner's available time. Also responsible for explaining the reasoning behind the plan.

**Core user actions identified from the scenario:**

1. **Add pet and owner information** — The user can enter their name and basic details about their pet (name, species, age, etc.). This establishes the context the scheduler needs to personalize care recommendations.

2. **Add and edit care tasks** — The user can create pet care tasks such as walks, feeding, medication, grooming, and enrichment. Each task includes at least a duration and a priority level, and the user can update these as needs change.

3. **Generate a daily care schedule** — The user can request a daily plan that organizes their tasks based on constraints like available time and task priority. The system produces a clear schedule and explains the reasoning behind its choices.

**b. Design changes**

Yes, two changes were made after an AI-assisted review of the initial skeleton:

1. **Added `ScheduledTask` class** — The original design had `generate_schedule()` returning a plain `list[Task]`, but there was no way to know *when* each task starts in the day. A new `ScheduledTask` dataclass was introduced to pair each task with its `start_minute`, making the schedule displayable as a timeline.

2. **Added `scheduled_tasks` attribute to Scheduler** — Originally `generate_schedule()` returned a list but the Scheduler didn't store it. This meant `explain_plan()` had no access to the generated schedule. Adding `self.scheduled_tasks` lets both methods share state so the explanation can reference the actual plan.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
