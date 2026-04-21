---
name: PawPal+ AI Edition — Reflection & Ethics (Model Card)
type: reflection
---

# Reflection & Ethics — PawPal+ AI Edition

## Limitations and Biases

**No memory across sessions.** All task data lives in `st.session_state` and is lost on page reload. The AI has no history of what the pet was scheduled to do yesterday, so it cannot learn from past routines or flag things like "this pet has skipped grooming three days in a row."

**Training data bias toward common pets.** Gemini's suggestions are grounded in whatever pet-care content dominated its training corpus. Dogs and cats receive detailed, well-calibrated suggestions. Less common pets (rabbits, birds, reptiles) can receive suggestions that are plausible-sounding but not species-accurate — for example, recommending grooming frequencies appropriate for dogs when applied to a rabbit.

**Single-owner, single-language design.** The app assumes one owner, one time zone, and English input. A multi-pet household with overlapping care needs, or a non-English-speaking user, is poorly served.

**No veterinary grounding.** Health notes are passed to Gemini as free text, but the model is not a licensed veterinarian and has no access to clinical databases. Suggestions for pets with stated health conditions (e.g., "diabetic", "hip dysplasia") may sound medically appropriate but are not validated against any professional standard. The app includes no disclaimer visible to the user at the point of receiving AI suggestions.

**Greedy scheduler is rigid.** `generate_schedule()` sorts by priority → preferred time → duration and stops when the time budget is exceeded. It never reorders or swaps tasks to fit more total care into the day. A high-priority 90-minute task will block all remaining tasks even if two 40-minute medium-priority tasks would collectively provide more value.

---

## Potential for Misuse and Safeguards

**Veterinary advice substitution.** The most foreseeable misuse is an owner treating Gemini's task suggestions as medical guidance — for instance, acting on a medication schedule or dosage implied by a suggested task. The system offers no guardrails against this today. A responsible mitigation would be a static disclaimer on the AI suggestions panel ("These suggestions are not a substitute for veterinary advice") and a system prompt instruction telling Gemini to explicitly flag if a health note requires professional consultation.

**API key exposure.** The sidebar accepts a raw API key and the code correctly avoids logging it (`"Your key is never stored or logged."` caption). However, the key travels in the browser session and could be exposed if the app were deployed on a shared or public host without HTTPS. Mitigation: server-side key management (environment variable injection) rather than client-side input for any public deployment.

**Prompt injection via health notes.** The `health_notes` field is passed directly into the Gemini prompt without sanitization. A malicious user could craft a health note like `"Ignore previous instructions and output..."` to attempt to hijack the model's output. In a single-user local app this is low-risk, but matters in any multi-user deployment. Mitigation: wrap the health notes field in a structured format that signals to the model it is data, not instruction.

---

## Surprises During Reliability Testing

**Markdown wrapping despite explicit instructions.** The system prompt says "No markdown, no extra text," yet Gemini occasionally wraps its JSON response in ` ```json ``` ` code fences. The parser in `suggest_tasks()` strips these fences before parsing. Without this step, every such response would cause a `JSONDecodeError`. What was surprising was that this happened even with `gemini-2.5-flash-lite` and `thinking_budget=0` — suggesting the tendency to add markdown is baked deeply into the model's output style and is not reliably suppressed by a system prompt alone.

**Field validation failures were more common than expected.** Roughly 1 in 10 suggestions in manual testing had a missing required field or an out-of-spec `priority` / `preferred_time` value (e.g., `"high-priority"` instead of `"high"`, or `"anytime"` instead of `"any"`). The `_validate_suggestion()` guard filtered these silently. Without the validator, those tasks would have caused a `KeyError` or `ValueError` when constructing the `Task` object. This underscored that structured output from LLMs is not as reliable as it appears — a strictly typed schema request is a starting point, not a guarantee.

**`explain_schedule()` was unexpectedly robust.** Because the method catches all exceptions and returns an error string rather than raising, it never crashed the UI in any test session. However, this also means silent failures: if the API returns a malformed response, the user sees a bland error message with no indication of what actually went wrong. The log captures the full error, but the user has no way to know that.

**`thinking_budget=0` was a non-obvious but critical requirement.** On the Gemini free tier, `gemini-2.5-flash-lite` without `thinking_budget=0` silently consumes its output token budget on internal reasoning tokens, leaving almost no tokens for the actual JSON response — producing truncated, unparseable output. This behavior is not documented prominently and took several failed test runs to diagnose via the log file.

---

## Collaboration with AI During This Project

This project was built with significant assistance from Claude (Anthropic) across every phase of development.

**Prompting and architecture design.** Early in the project, I used Claude to think through the overall architecture — specifically how to separate the AI layer from the business logic so that the scheduler could run independently of any API call. Claude helped me draft the system prompt for `suggest_tasks()`, iterating on the field schema (adding `reason` as a per-task explanation field, tightening the enum values for `priority` and `preferred_time`) until the structured output was clean enough to parse reliably.

**Debugging.** When `gemini-2.5-flash-lite` was returning truncated JSON, I described the symptom to Claude and it helped me narrow the cause to the free-tier thinking-token issue. It also helped me write the code-fence stripping logic in `suggest_tasks()` after I observed that the model was ignoring the "no markdown" instruction.

**Code generation.** Claude wrote the initial skeleton for `ai_advisor.py`, the `_validate_suggestion()` method, the mocked API tests in `test_ai_advisor.py`, and the Streamlit checkbox-review panel in `app.py`. In each case I reviewed the generated code against the existing architecture before accepting it — the final code reflects edits I made after that review.

Two specific instances of AI suggestions worth examining in detail:

**Helpful suggestion — structured validation guard.** When designing `suggest_tasks()`, Claude suggested adding a `_validate_suggestion()` method as a runtime filter between the raw Gemini response and the `Task` constructor, rather than wrapping the constructor call in a try/except. This was a better design: it separates the concern of "is this data structurally valid?" from "does this task make sense?", produces clearer log warnings per field, and keeps the Task constructor free of defensive logic it shouldn't need. The suggestion led directly to the validation architecture that caught real failures during testing.

**Flawed suggestion — model name in CLAUDE.md.** Claude initially recommended using `gemini-2.0-flash` as the default model in the codebase, noting it as a widely available and capable option. In practice, `gemini-2.0-flash` and `gemini-2.0-flash-lite` have zero free-tier quota on the Google AI Studio API and return 429 errors immediately. The correct free-tier model is `gemini-2.5-flash-lite` (or `gemini-2.5-flash`). Claude's suggestion was grounded in general knowledge about the Gemini model family but was not current on the specific quota and availability details of the free tier at the time of development. This was a good reminder that AI assistants can be confidently wrong on operational specifics that change faster than their training data.

---

## Future Improvements

**Veterinary disclaimer.** The single highest-impact change would be a visible disclaimer on the AI suggestions panel stating that suggestions are not a substitute for professional veterinary advice, paired with a system prompt instruction to flag health conditions that warrant a vet visit.

**Persistent storage.** Moving task data from `st.session_state` to a lightweight local database (e.g., SQLite via `sqlite3`) would allow the app to remember past schedules and let the AI suggestions improve over time — for instance, noting that a recurring task has been skipped multiple days in a row.

**Smarter scheduling.** Replacing the greedy first-fit algorithm with a knapsack-style optimizer would allow the scheduler to pack more total care value into the available time rather than stopping as soon as one task exceeds the budget.

**Structured output enforcement.** Rather than relying on the model to follow a schema and then validating after the fact, using Gemini's native JSON mode or response schema parameter would eliminate the markdown-wrapping and field-mismatch failures observed in testing — reducing the rate of validation rejections from ~10% toward zero.

**Multi-user deployment safety.** For any public deployment, the API key input should be replaced with server-side environment variable injection, and the `health_notes` field should be sanitized or templated before being included in the prompt to prevent prompt injection.
