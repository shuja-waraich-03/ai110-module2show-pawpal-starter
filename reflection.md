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

The scheduler considers three main constraints:
- **Priority** — Tasks ranked high/medium/low determine scheduling order. High-priority tasks (medication, feeding) are placed first to guarantee they fit within available time.
- **Available time** — The owner's `available_minutes` acts as a hard cap. The scheduler greedily fills the time budget and skips tasks that won't fit.
- **Preferred time** — Each task can specify an "HH:MM" slot. When sorting by time, the scheduler respects the owner's preferred daily routine order.

Priority was treated as the most important constraint because missing a high-priority task like medication has real consequences, while rearranging task order is merely inconvenient.

**b. Tradeoffs**

The conflict detector checks for **exact preferred_time matches** (e.g., two tasks both at "07:30") rather than computing whether time windows actually overlap based on duration. For example, a 30-minute task at "07:00" and a 5-minute task at "07:15" are not flagged as conflicting, even though the first task wouldn't finish until 07:30.

This tradeoff was a deliberate choice after reviewing an AI suggestion to add full overlap detection based on `start_minute` ranges. That version was more thorough but also more complex — and in our scheduler, tasks are placed sequentially (one after another), so `start_minute` windows never truly overlap. The overlap check was dead code. Removing it kept the method simpler and honest about what it actually detects: same-slot collisions and back-to-back category stacking. For a pet care app where tasks are approximate ("morning walk sometime around 7:30"), exact-match detection is sufficient and easier to reason about.

**AI refinement note:** An initial version of `_detect_conflicts` included an overlapping time-window check (`a.start_minute < b.start_minute < a_end`). On review, this could never trigger because the scheduler places tasks sequentially with no gaps. A more "Pythonic" version using `itertools.combinations` was also considered — it's more concise but harder to read for someone unfamiliar with itertools. The explicit index-based loop was kept for clarity.

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
