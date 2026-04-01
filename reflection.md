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

AI tools were used across every phase of this project, each time in a dedicated context to keep the work focused:

- **Phase 1 (Design)** — A fresh chat session was used to brainstorm the class structure. Prompting with the scenario description and asking "What classes and relationships would you design for a pet care scheduler?" produced the initial five-class UML skeleton. A follow-up prompt asking for a review of the skeleton caught the missing `ScheduledTask` wrapper and the need for `scheduled_tasks` state on the Scheduler.
- **Phase 2 (Implementation)** — A separate session focused on turning stubs into working code. The most effective prompts were targeted requests like "Implement `generate_schedule` with a greedy time-budget algorithm that supports four sort strategies." This kept suggestions scoped to one method at a time rather than rewriting entire files.
- **Phase 3 (Testing)** — Another session was started specifically for test planning. Asking "What are the most important edge cases to test for a pet scheduler with sorting and recurring tasks?" produced a prioritized list that mapped directly to the test functions written. Copilot's inline completions were especially fast for generating the repetitive setup code (creating `Pet`, `Task`, `Owner` fixtures) once the first test established the pattern.
- **Phase 4 (UI)** — A final session was used to wire backend features to Streamlit. Prompting with `#file:pawpal_system.py` and asking which Scheduler methods were not yet exposed in the UI quickly identified the gaps (filter dropdowns, sort selector, conflict warnings, task completion).

**Which Copilot features were most effective:**

1. **`#codebase` context** — Letting Copilot see the full project when asking architectural questions ("Does my UML still match my code?") produced accurate, file-specific answers rather than generic advice.
2. **Inline completions** — Once a pattern was established (e.g., the first test function), Copilot reliably completed subsequent test functions with correct fixture setup and assertions, saving significant boilerplate typing.
3. **Chat-based code review** — Asking "Review this method for edge cases I missed" surfaced the empty-`preferred_time` crash risk in `sort_by_time` before it became a bug.

**b. Judgment and verification**

**Example of a rejected suggestion:** When generating the conflict detection logic, Copilot suggested using `itertools.combinations` to check all task pairs and also included an overlapping time-window check that computed whether one task's `start_minute + duration` encroached on another task's `start_minute`. On review, this overlap check could never trigger — the scheduler places tasks sequentially with no gaps, so time windows never actually overlap by construction. Including it would have been dead code that misleads future readers into thinking overlap is a real scenario. The suggestion was rejected and replaced with the simpler exact-match check on `preferred_time`, which is what actually matters for a pet care routine where times are approximate.

**How suggestions were verified:** Every AI-generated code block was reviewed by (1) reading it line-by-line before accepting, (2) tracing through at least one concrete example mentally (e.g., "if task A is at 08:00 and task B is at 08:00, does this produce the right warning?"), and (3) running the test suite after integration. The tests served as the final verification gate — if a suggestion introduced a regression, the failing test caught it immediately.

**How separate chat sessions helped:** Starting a new session for each phase (design, implementation, testing, UI) prevented context bleed. The testing session didn't carry assumptions from the implementation session, which meant it could independently identify behaviors worth verifying rather than just confirming what was already written. It also kept each conversation short enough that Copilot's suggestions stayed relevant to the current task instead of drifting.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers 15 tests across four behavioral areas:

1. **Sorting correctness (4 tests)** — Chronological ordering by `preferred_time`, empty-time-last behavior, priority-first sort, and shortest-first sort. These are important because an incorrect sort order means the owner's most critical tasks could be pushed to the end and dropped when time runs out.

2. **Recurrence logic (4 tests)** — Daily tasks produce a next-day copy, weekly tasks recur in 7 days, as-needed tasks return `None`, and `Pet.complete_task()` appends the next occurrence. These matter because a recurrence bug means tasks silently disappear from the schedule — the owner misses a medication day and doesn't realize it.

3. **Conflict detection (3 tests)** — Same-time collision for one pet, same-time collision across different pets (with the cross-pet warning), and back-to-back same-category flagging. Without these, the schedule would look valid even when it contains impossible overlaps.

4. **Time budget / overflow (2 tests)** — Tasks exceeding `available_minutes` are excluded; zero minutes yields an empty schedule. This ensures the scheduler never over-commits the owner's time and handles the degenerate case gracefully.

**b. Confidence**

**4 out of 5 stars.** All core scheduling algorithms — sorting, recurrence, conflict detection, and time budgeting — are tested and passing. The star is withheld because the suite does not yet cover:

- **Malformed input** — What happens if `preferred_time` is "abc" instead of "HH:MM"? The current `split(":")` would crash.
- **UI integration** — The Streamlit layer is untested; a widget misconfiguration could silently pass the wrong value to the backend.
- **Multi-pet scheduling interactions** — Beyond conflict detection, edge cases like two pets with identical task names or an owner with 10+ pets and 50+ tasks are unexplored.

---

## 5. Reflection

**a. What went well**

The separation between backend logic (`pawpal_system.py`) and UI (`app.py`) is the part I'm most satisfied with. Every scheduling algorithm, filter, and conflict check lives in the system module with no Streamlit dependency, which made it straightforward to test with pure pytest and then wire into the UI as a separate step. The `Scheduler` class acts as a clean API boundary — the UI calls `generate_schedule()`, reads `scheduled_tasks` and `conflicts`, and renders them. This separation meant the backend could be completed and verified before touching the UI at all.

**b. What you would improve**

Two things:

1. **Input validation** — The system trusts that `preferred_time` is always a valid "HH:MM" string or empty. A `Task.__post_init__` validator should parse and reject bad formats early rather than letting them propagate to `sort_by_time` where the crash would be confusing.

2. **Persistent state** — Currently everything resets when the Streamlit app reruns. Adding a simple JSON or SQLite persistence layer would let the owner close the browser and come back to their schedule. The class structure already supports serialization — each dataclass has simple fields — so the effort would be modest.

**c. Key takeaway**

The most important lesson was that **being the lead architect means deciding what *not* to build, not just what to build.** AI tools like Copilot generate suggestions quickly and confidently, but they optimize for completeness — they will happily add overlap detection that can never trigger, `itertools` abstractions for two-line loops, and error handling for impossible states. The architect's job is to evaluate each suggestion against the actual system constraints and reject the ones that add complexity without value. Saying "no" to a correct-but-unnecessary suggestion is harder than saying "no" to a wrong one, and that judgment is the core skill that AI collaboration demands.
