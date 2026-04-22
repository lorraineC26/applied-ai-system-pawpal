import json
import logging
import os
from google import genai
from google.genai import types

logging.basicConfig(
    filename="petnest_advisor.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

_REQUIRED_FIELDS = {"name", "category", "duration", "priority", "preferred_time", "time"}
_VALID_PRIORITY = {"high", "medium", "low"}
_VALID_PREFERRED_TIME = {"morning", "afternoon", "evening", "any"}

_SUGGEST_SYSTEM = (
    "Suggest daily pet care tasks as a JSON array only. "
    "Each item: name, category (feeding/exercise/medication/grooming/enrichment/hygiene/veterinary/other), "
    "duration (int minutes), priority (high/medium/low), "
    "preferred_time (morning/afternoon/evening/any), time (HH:MM), reason (one sentence). "
    "No markdown, no extra text."
)

_EXPLAIN_SYSTEM = (
    "You are a pet care advisor. In 2-3 sentences explain today's plan to the owner. "
    "Focus on benefits for this pet and note any skipped tasks. Be warm and brief."
)


class AIAdvisor:
    def __init__(self, api_key=None, model="gemini-2.5-flash-lite"):
        self.model_name = model
        self.client = genai.Client(api_key=api_key or os.environ.get("GOOGLE_API_KEY"))

    def _validate_suggestion(self, s):
        """Return True if s has all required fields with valid values."""
        if not _REQUIRED_FIELDS.issubset(s.keys()):
            missing = _REQUIRED_FIELDS - s.keys()
            logger.warning("validate_suggestion | rejected — missing fields: %s", missing)
            return False
        if s["priority"] not in _VALID_PRIORITY:
            logger.warning("validate_suggestion | rejected — invalid priority: %s", s["priority"])
            return False
        if s["preferred_time"] not in _VALID_PREFERRED_TIME:
            logger.warning("validate_suggestion | rejected — invalid preferred_time: %s", s["preferred_time"])
            return False
        try:
            if int(s["duration"]) <= 0:
                raise ValueError
        except (ValueError, TypeError):
            logger.warning("validate_suggestion | rejected — invalid duration: %s", s["duration"])
            return False
        return True

    def suggest_tasks(self, pet, time_available):
        """
        Suggest care tasks for a pet given the owner's available time.

        Returns a list of dicts with keys: name, category, duration, priority,
        preferred_time, time, reason. Returns [] on JSON parse failure.
        Raises on API-level failures.
        """
        user_msg = (
            f"Pet: {pet.name}, {pet.species}, age {pet.age}\n"
            f"Health: {pet.health_notes or 'None'}\n"
            f"Time available: {time_available} min"
        )
        logger.info(
            "suggest_tasks | pet=%s species=%s age=%s time_budget=%d",
            pet.name, pet.species, pet.age, time_available,
        )
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=user_msg,
            config=types.GenerateContentConfig(
                system_instruction=_SUGGEST_SYSTEM,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
        raw = response.text.strip()
        # Strip markdown code fences if the model wraps the JSON anyway
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
        logger.info("suggest_tasks | raw_response_length=%d", len(raw))
        try:
            tasks = json.loads(raw)
            logger.info("suggest_tasks | parsed %d tasks", len(tasks))
            valid = [t for t in tasks if self._validate_suggestion(t)]
            if len(valid) < len(tasks):
                logger.warning(
                    "suggest_tasks | dropped %d invalid suggestion(s)", len(tasks) - len(valid)
                )
            return valid
        except json.JSONDecodeError as e:
            logger.error(
                "suggest_tasks | JSON parse error: %s | raw_start=%s", e, raw[:300]
            )
            return []

    def explain_schedule(self, schedule, owner):
        """
        Generate a plain-English explanation of a finalized schedule.

        Returns the explanation string. Never raises — returns an error
        message string on failure.
        """
        pet_profiles = "\n".join(
            "  • {name}: {species}, age {age}{notes}".format(
                name=p.name,
                species=p.species,
                age=p.age,
                notes=f", notes: {p.health_notes}" if p.health_notes else "",
            )
            for p in owner.pets
        )
        included = "\n".join(
            f"  • {t.name} — {t.duration} min, {t.priority} priority"
            for t in schedule.tasks
        )
        skipped_lines = [
            f"  • {name}: {reason}"
            for name, reason in schedule.reasoning.items()
            if reason.startswith("Skipped")
        ]
        user_msg = (
            f"Owner: {owner.name}, budget: {owner.time_available} min\n"
            f"Pets: {pet_profiles}\n"
            f"Scheduled ({schedule.total_duration} min): {included}"
        )
        if skipped_lines:
            user_msg += "\nSkipped: " + "; ".join(skipped_lines)

        logger.info(
            "explain_schedule | owner=%s pets=%d tasks_scheduled=%d tasks_skipped=%d",
            owner.name, len(owner.pets), len(schedule.tasks), len(skipped_lines),
        )
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=user_msg,
                config=types.GenerateContentConfig(
                    system_instruction=_EXPLAIN_SYSTEM,
                    max_output_tokens=300,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                ),
            )
            explanation = response.text.strip()
            logger.info("explain_schedule | response_length=%d", len(explanation))
            return explanation
        except Exception as e:
            logger.error("explain_schedule | error: %s", e)
            return f"Unable to generate explanation: {e}"
