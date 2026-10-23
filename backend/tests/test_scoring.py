from decimal import Decimal

import pytest

from quiz.models import ScoreLevel
from quiz.services import compute_percent, score_bounds

pytestmark = pytest.mark.django_db


def best_letters(data):
    return {q["number"]: next(o["letter"] for o in q["options"] if o["points"] == 7) for q in data["questions"]}


def worst_letters(data):
    return {q["number"]: min(q["options"], key=lambda o: o["points"])["letter"] for q in data["questions"]}


def test_bounds_and_percent():
    assert score_bounds(35) == (105, 245)
    assert compute_percent(245, 35) == Decimal("100.0")
    assert compute_percent(105, 35) == Decimal("0.0")
    assert compute_percent(0, 35) == Decimal("0.0")
    assert compute_percent(80, 35) == Decimal("0.0")  # 105 dan past – 0%
    assert compute_percent(175, 35) == Decimal("50.0")
    assert compute_percent(182, 35) == Decimal("55.0")


@pytest.mark.parametrize(
    "score,expected",
    [(0, "Boshlang‘ich"), (139, "Boshlang‘ich"), (140, "O‘rta"), (174, "O‘rta"), (175, "Yuqori"),
     (209, "Yuqori"), (210, "Juda yuqori"), (234, "Juda yuqori"), (235, "A’lo"), (245, "A’lo")],
)
def test_default_levels(score, expected):
    assert ScoreLevel.for_score(score).name_uz == expected


def test_all_correct_gives_245(client, make_attempt, answer, questions_data):
    attempt_id, token = make_attempt()
    for number, letter in best_letters(questions_data).items():
        assert answer(attempt_id, token, number, letter).status_code == 200
    resp = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    data = resp.json()
    assert resp.status_code == 200
    assert data["total_score"] == 245
    assert data["max_score"] == 245
    assert data["percent"] == 100.0
    assert data["level"]["name_uz"] == "A’lo"
    assert data["answered_count"] == 35
    cats = {c["key"]: c for c in data["categories"]}
    assert cats["numeric"]["max"] == 7 * 7
    assert cats["pattern"]["max"] == 17 * 7
    assert cats["spatial"]["max"] == 11 * 7
    assert all(c["percent"] == 100.0 for c in cats.values())


def test_all_lowest(client, make_attempt, answer, questions_data):
    # questions.json da 7-savolning eng past bali 4, shuning uchun eng kichik to‘liq ball 106.
    expected = sum(min(o["points"] for o in q["options"]) for q in questions_data["questions"])
    attempt_id, token = make_attempt()
    for number, letter in worst_letters(questions_data).items():
        answer(attempt_id, token, number, letter)
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == expected
    assert data["percent"] == float(compute_percent(expected, 35))
    assert data["level"]["name_uz"] == "Boshlang‘ich"


def test_unanswered_is_zero(client, make_attempt):
    attempt_id, token = make_attempt()
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == 0
    assert data["percent"] == 0.0
    assert data["answered_count"] == 0


def test_score_matches_json_for_each_option(client, make_attempt, answer, questions_data):
    """Har bir savol uchun aralash javoblar: yig‘indi questions.json ballari bilan bir xil."""
    attempt_id, token = make_attempt()
    expected = 0
    for i, q in enumerate(questions_data["questions"]):
        if i % 5 == 4:
            continue  # bu savollarga javob berilmaydi → 0 ball
        option = q["options"][i % 6]
        expected += option["points"]
        answer(attempt_id, token, q["number"], option["letter"])
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == expected
    assert data["answered_count"] == 28


def test_changing_answer_replaces_previous(client, make_attempt, answer, questions_data):
    attempt_id, token = make_attempt()
    q1 = questions_data["questions"][0]
    by_letter = {o["letter"]: o["points"] for o in q1["options"]}
    answer(attempt_id, token, 1, "B")
    answer(attempt_id, token, 1, "C")
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == by_letter["C"]


def test_clearing_answer(client, make_attempt, answer):
    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "C")
    resp = answer(attempt_id, token, 1, None)
    assert resp.status_code == 200
    assert resp.json()["answered_count"] == 0
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == 0


def test_finish_is_idempotent(client, make_attempt, answer):
    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "C")
    first = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    second = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert first["total_score"] == second["total_score"] == 7
    assert first["finished_at"] == second["finished_at"]


def test_inactive_question_not_counted(client, make_attempt, answer):
    from quiz.models import Question

    Question.objects.filter(number=35).update(is_active=False)
    attempt_id, token = make_attempt()
    resp = client.get(f"/api/v1/attempts/{attempt_id}/questions", HTTP_X_ATTEMPT_TOKEN=token)
    assert len(resp.json()["questions"]) == 34
    assert answer(attempt_id, token, 35, "A").status_code == 404
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["max_score"] == 34 * 7
