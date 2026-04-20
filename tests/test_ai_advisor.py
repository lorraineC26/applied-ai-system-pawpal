import json
from unittest.mock import MagicMock, patch
import pytest

from ai_advisor import AIAdvisor


def _make_advisor():
    with patch("ai_advisor.genai.Client"):
        return AIAdvisor(api_key="test-key")


def _mock_response(text):
    r = MagicMock()
    r.text = text
    return r


VALID_TASK = {
    "name": "Morning walk",
    "category": "exercise",
    "duration": 20,
    "priority": "high",
    "preferred_time": "morning",
    "time": "08:00",
    "reason": "Good for cardiovascular health.",
}


# ---------------------------------------------------------------------------
# suggest_tasks tests
# ---------------------------------------------------------------------------

def test_valid_json_returns_task_list():
    advisor = _make_advisor()
    payload = json.dumps([VALID_TASK])
    advisor.client.models.generate_content.return_value = _mock_response(payload)
    result = advisor.suggest_tasks(MagicMock(name="Rex", species="dog", age=3, health_notes=""), 60)
    assert len(result) == 1
    assert result[0]["name"] == "Morning walk"


def test_filters_invalid_suggestions():
    advisor = _make_advisor()
    bad_task = {"name": "Bad task", "duration": 10}  # missing required fields
    payload = json.dumps([VALID_TASK, bad_task])
    advisor.client.models.generate_content.return_value = _mock_response(payload)
    result = advisor.suggest_tasks(MagicMock(name="Rex", species="dog", age=3, health_notes=""), 60)
    assert len(result) == 1
    assert result[0]["name"] == "Morning walk"


def test_json_parse_failure_returns_empty():
    advisor = _make_advisor()
    advisor.client.models.generate_content.return_value = _mock_response("not json at all")
    result = advisor.suggest_tasks(MagicMock(name="Rex", species="dog", age=3, health_notes=""), 60)
    assert result == []


def test_strips_markdown_code_fences():
    advisor = _make_advisor()
    wrapped = f"```json\n{json.dumps([VALID_TASK])}\n```"
    advisor.client.models.generate_content.return_value = _mock_response(wrapped)
    result = advisor.suggest_tasks(MagicMock(name="Rex", species="dog", age=3, health_notes=""), 60)
    assert len(result) == 1


# ---------------------------------------------------------------------------
# explain_schedule tests
# ---------------------------------------------------------------------------

def test_explain_schedule_returns_string():
    advisor = _make_advisor()
    advisor.client.models.generate_content.return_value = _mock_response("Great plan for your dog!")
    schedule = MagicMock(tasks=[], total_duration=0, reasoning={})
    owner = MagicMock(name="Jordan", time_available=120, pets=[])
    result = advisor.explain_schedule(schedule, owner)
    assert isinstance(result, str)
    assert "Great plan" in result


def test_explain_schedule_handles_api_error():
    advisor = _make_advisor()
    advisor.client.models.generate_content.side_effect = Exception("API down")
    schedule = MagicMock(tasks=[], total_duration=0, reasoning={})
    owner = MagicMock(name="Jordan", time_available=120, pets=[])
    result = advisor.explain_schedule(schedule, owner)
    assert isinstance(result, str)
    assert "Unable" in result
