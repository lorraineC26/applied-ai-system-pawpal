# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run tests
python -m pytest tests/test_petnest.py -v

# Run a single test
python -m pytest tests/test_petnest.py::test_function_name -v

# CLI demo (manual logic testing without UI)
python main.py
```

No linter is configured. Python 3.9+ required.

## Project Extension

The project is being extended in phases per `project_requirements.md`. 

The existing README and reflections files for the original project are in the `applied-ai-system-pawpal/public/original_repo` directory, which named `README_origin_repo.md` and `reflections_origin.md` in this repo. 

## Architecture

The project is a Streamlit pet care scheduler with two main files:

**[petnest_system.py](petnest_system.py)** — all business logic. Five classes:
- `Owner` — holds `name`, `time_available` (minutes), and a list of `Pet` objects. The `.tasks` property aggregates all tasks across all pets.
- `Pet` — holds `name`, `species`, `age`, `health_notes`, and a list of `Task` objects.
- `Task` — holds scheduling attributes: `name`, `category`, `duration`, `priority` (`"high"/"medium"/"low"`), `preferred_time` (`"morning"/"afternoon"/"evening"/"any"`), `time` (HH:MM string), `recurrence` (`"daily"/"weekly"/"none"`), `due_date`, `completed`. `mark_complete()` returns a new task with advanced `due_date` for recurring tasks.
- `Schedule` — data container: sorted task list, total duration, and per-task reasoning dict.
- `Scheduler` — takes an `Owner`; key methods: `generate_schedule()` (greedy first-fit sorted by priority→preferred_time→duration), `sort_by_time()` (chronological by HH:MM), `filter_tasks()` (by completion/pet), `detect_conflicts()` (groups by `time` field), `explain_plan()`.

**[ai_advisor.py](ai_advisor.py)** — Phase 1 AI layer. `AIAdvisor` class wraps Google Gemini via `google-genai` SDK (`genai.Client`). Two methods:
- `suggest_tasks(pet, time_available)` — calls Gemini to generate a JSON array of suggested tasks for a pet; strips markdown fences, returns list of dicts or `[]` on failure.
- `explain_schedule(schedule, owner)` — calls Gemini to produce a 2–3 sentence natural-language summary of the built schedule.
- Model: `gemini-2.5-flash` with `thinking_budget=0` (required to prevent thinking tokens consuming the output budget on free tier). API key read from sidebar input or `GOOGLE_API_KEY` env var. All calls logged to `petnest_advisor.log`.

**[app.py](app.py)** — Streamlit UI. Reads/writes `st.session_state` for all pet and task data (no persistence across reloads). Constructs `Owner`/`Pet`/`Task` objects from session state, calls `Scheduler`, and renders results. Phase 1 additions: sidebar API key input; "Get AI Suggestions" button (Step 1) → checkbox list → "Add selected" button; "Explain plan with AI" button (Step 3) after schedule is built.

**[tests/test_petnest.py](tests/test_petnest.py)** — 13 unit tests covering task completion, chronological sorting, recurrence (daily/weekly/none), and conflict detection. `generate_schedule()` time-budget logic has no automated tests.

## Known Issues

- `explain_plan()` references `self.owner.pet` (singular) — crashes for multi-pet owners; correct attribute is `self.owner.pets`.
- Task data does not persist across Streamlit page reloads (session state only).
- Gemini free-tier quota: `gemini-2.5-flash-lite` requires `thinking_budget=0` or thinking tokens will consume `max_output_tokens` and truncate JSON output. `gemini-2.0-flash` and `gemini-2.0-flash-lite` have 0 free-tier quota (429 errors).

