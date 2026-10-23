"""Test davomida API javoblarida ball yoki to‘g‘ri javob chiqmasligini tekshiradi."""

import json

import pytest

pytestmark = pytest.mark.django_db

FORBIDDEN_KEYS = {"points", "correct", "is_correct", "reason_uz", "reason_ru", "logic_uz", "logic_ru", "score"}


def walk_keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield k
            yield from walk_keys(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk_keys(v)


def assert_no_secrets(payload, questions_data):
    keys = set(walk_keys(payload))
    assert not keys & FORBIDDEN_KEYS, keys & FORBIDDEN_KEYS
    text = json.dumps(payload, ensure_ascii=False)
    for q in questions_data["questions"]:
        assert q["logic_uz"] not in text
        for o in q["options"]:
            if o.get("reason_uz"):
                assert o["reason_uz"] not in text


def test_meta_has_no_secrets(client, imported, questions_data):
    data = client.get("/api/v1/test/meta").json()
    assert data["question_count"] == 35
    assert_no_secrets(data, questions_data)


def test_create_attempt_has_no_secrets(client, imported, questions_data):
    resp = client.post("/api/v1/attempts", {"full_name": "Ali Valiyev"}, format="json")
    assert_no_secrets(resp.json(), questions_data)


def test_questions_have_no_points_or_correct(client, make_attempt, answer, questions_data):
    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "C")
    resp = client.get(f"/api/v1/attempts/{attempt_id}/questions", HTTP_X_ATTEMPT_TOKEN=token)
    data = resp.json()
    assert resp.status_code == 200
    assert len(data["questions"]) == 35
    assert data["answers"] == {"1": "C"}
    for q in data["questions"]:
        assert set(q.keys()) == {"number", "type", "prompt", "figure", "options"}
        assert len(q["options"]) == 6
        for o in q["options"]:
            assert set(o.keys()) == {"letter", "value", "image"}
    assert_no_secrets(data, questions_data)


def test_answer_response_has_no_secrets(make_attempt, answer, questions_data):
    attempt_id, token = make_attempt()
    data = answer(attempt_id, token, 1, "C").json()
    assert set(data.keys()) == {"number", "letter", "answered_count"}
    assert_no_secrets(data, questions_data)


def test_result_does_not_reveal_correct_answers(client, make_attempt, answer, questions_data):
    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "A")
    client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    data = client.get(f"/api/v1/attempts/{attempt_id}/result", HTTP_X_ATTEMPT_TOKEN=token).json()
    keys = set(walk_keys(data))
    assert not keys & {"points", "correct", "is_correct", "answers", "options"}
    text = json.dumps(data, ensure_ascii=False)
    assert "reason" not in text and "logic" not in text


def test_option_values_match_json(client, make_attempt, questions_data):
    """Rasmlar va sonlar json bilan bir xil (ballarsiz)."""
    attempt_id, token = make_attempt()
    data = client.get(f"/api/v1/attempts/{attempt_id}/questions", HTTP_X_ATTEMPT_TOKEN=token).json()
    by_number = {q["number"]: q for q in data["questions"]}
    for q in questions_data["questions"]:
        api_q = by_number[q["number"]]
        assert api_q["type"] == q["type"]
        assert api_q["prompt"] == q["prompt"]
        assert api_q["figure"].endswith(q["figure"].split("/", 1)[1])
        for src, dst in zip(q["options"], api_q["options"]):
            assert src["letter"] == dst["letter"]
            if q["type"] == "number":
                assert dst["value"] == src["value"]
            else:
                assert dst["image"].endswith(src["image"].split("/", 1)[1])
