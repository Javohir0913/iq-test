from decimal import ROUND_HALF_UP, Decimal

import pytest

from quiz.models import ScoreLevel
from quiz.services import percent_in_range, score_bounds

pytestmark = pytest.mark.django_db


def best_letters(data):
    return {q["number"]: next(o["letter"] for o in q["options"] if o["points"] == 7) for q in data["questions"]}


def worst_letters(data):
    return {q["number"]: min(q["options"], key=lambda o: o["points"])["letter"] for q in data["questions"]}


def test_bounds_and_percent():
    assert score_bounds(35) == (0, 245)
    assert percent_in_range(245, 105, 245) == Decimal("100.0")
    assert percent_in_range(105, 105, 245) == Decimal("0.0")
    assert percent_in_range(0, 105, 245) == Decimal("0.0")
    assert percent_in_range(80, 105, 245) == Decimal("0.0")  # eng pastdan ham past – 0%
    assert percent_in_range(175, 105, 245) == Decimal("50.0")
    assert percent_in_range(182, 105, 245) == Decimal("55.0")
    assert percent_in_range(Decimal("10.5"), 0, 21) == Decimal("50.0")


@pytest.mark.parametrize(
    "percent,expected",
    [(0, "Boshlang‘ich"), (24.9, "Boshlang‘ich"), (25, "O‘rta"), (49.9, "O‘rta"), (50, "Yuqori"),
     (74.9, "Yuqori"), (75, "Juda yuqori"), (92.9, "Juda yuqori"), (93, "A’lo"), (100, "A’lo")],
)
def test_default_levels(percent, expected):
    # Eski 35 savollik chegaralar (140/175/210/235 ball) foizga o‘tkazilgan
    assert ScoreLevel.for_percent(percent).name_uz == expected
    assert ScoreLevel.for_percent(percent).name_en


def test_all_correct_gives_max(client, make_attempt, answer, questions_data, bank_size):
    attempt_id, token = make_attempt()
    for number, letter in best_letters(questions_data).items():
        assert answer(attempt_id, token, number, letter).status_code == 200
    resp = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    data = resp.json()
    assert resp.status_code == 200
    assert data["total_score"] == bank_size * 7
    assert data["max_score"] == bank_size * 7
    assert data["percent"] == 100.0
    assert data["level"]["name_uz"] == "A’lo"
    assert data["answered_count"] == bank_size
    cats = {c["key"]: c for c in data["categories"]}
    for key in ("numeric", "pattern", "spatial"):
        count = sum(1 for q in questions_data["questions"] if q["category"] == key)
        assert cats[key]["max"] == count * 7
    assert all(c["percent"] == 100.0 for c in cats.values())


def test_all_lowest(client, make_attempt, answer, questions_data, bank_size):
    # questions.json da 7-savolning eng past bali 4, shuning uchun eng kichik to‘liq ball 106.
    expected = sum(min(o["points"] for o in q["options"]) for q in questions_data["questions"])
    attempt_id, token = make_attempt()
    for number, letter in worst_letters(questions_data).items():
        answer(attempt_id, token, number, letter)
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == expected
    assert data["percent"] == 0.0  # har savolda eng past variant – 0%
    assert data["level"]["name_uz"] == "Boshlang‘ich"


def test_unanswered_is_zero(client, make_attempt):
    attempt_id, token = make_attempt()
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["total_score"] == 0
    assert data["percent"] == 0.0
    assert data["answered_count"] == 0


def test_score_matches_json_for_each_option(client, make_attempt, answer, questions_data, bank_size):
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
    assert data["answered_count"] == sum(1 for i in range(bank_size) if i % 5 != 4)


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


def test_inactive_question_not_counted(client, make_attempt, answer, bank_size):
    from quiz.models import Question

    Question.objects.filter(number=35).update(is_active=False)
    attempt_id, token = make_attempt()
    resp = client.get(f"/api/v1/attempts/{attempt_id}/questions", HTTP_X_ATTEMPT_TOKEN=token)
    assert len(resp.json()["questions"]) == bank_size - 1
    assert answer(attempt_id, token, 35, "A").status_code == 404
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["max_score"] == (bank_size - 1) * 7


def _finish(client, attempt_id, token):
    return client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()


def test_difficulty_weights_multiply_points(client, make_attempt, answer, imported):
    from quiz.models import Attempt, Question, TestSettings

    s = TestSettings.load()
    s.weight_easy, s.weight_medium, s.weight_hard = Decimal("1"), Decimal("1.5"), Decimal("2")
    s.save()
    attempt_id, token = make_attempt()
    ids = Attempt.objects.get(pk=attempt_id).question_ids
    questions = list(Question.objects.filter(id__in=ids))
    hard = next(q for q in questions if q.difficulty == 3)
    best = hard.options.get(is_correct=True).letter
    assert answer(attempt_id, token, hard.number, best).status_code in (200, 201)
    data = _finish(client, attempt_id, token)
    weight = {1: Decimal("1"), 2: Decimal("1.5"), 3: Decimal("2")}
    expected_max = sum(7 * weight[q.difficulty] for q in questions)
    assert data["total_score"] == 14
    assert data["max_score"] == int(expected_max.quantize(Decimal(1), rounding=ROUND_HALF_UP))
    assert Attempt.objects.get(pk=attempt_id).max_score == data["max_score"]

    # Koeffitsient keyin o‘zgarsa – eski natijaning maks. bali o‘zgarmaydi
    s.weight_hard = Decimal("5")
    s.save()
    again = client.get(f"/api/v1/attempts/{attempt_id}/result", HTTP_X_ATTEMPT_TOKEN=token)
    if again.status_code == 200:
        assert again.json()["max_score"] == data["max_score"]


def test_zero_point_option_gives_no_score(client, make_attempt, answer, imported):
    from quiz.models import Attempt, Option, Question

    attempt_id, token = make_attempt()
    q = Question.objects.get(id=Attempt.objects.get(pk=attempt_id).question_ids[0])
    worst = q.options.order_by("points").first()
    Option.objects.filter(pk=worst.pk).update(points=0)
    assert answer(attempt_id, token, q.number, worst.letter).status_code in (200, 201)
    data = _finish(client, attempt_id, token)
    assert data["total_score"] == 0
    assert data["percent"] == 0.0


def test_zero_points_allowed_in_admin_validation(imported):
    from quiz.models import Question

    q = Question.objects.first()
    options = list(q.options.all())
    lowest = min(options, key=lambda o: o.points)
    lowest.points = 0
    q.clean_options(options)  # xato chiqmasligi kerak


def test_settings_page_shows_stage_counts_and_weights(admin_client):
    from quiz.models import TestSettings

    html = admin_client.get(f"/admin/quiz/testsettings/{TestSettings.load().pk}/change/").content.decode()
    for text in ["oson savollar", "qiyin savollar", "koeffitsienti", "taklif qilinadigan do‘stlar"]:
        assert text in html.lower() or text in html, text


def test_lowered_correct_points_still_reach_100_percent(client, make_attempt, answer, imported):
    """To‘g‘ri javob 5 ballga tushirilsa ham, hammasi to‘g‘ri – 100%."""
    from quiz.models import Attempt, Option, Question

    attempt_id, token = make_attempt()
    ids = Attempt.objects.get(pk=attempt_id).question_ids
    q = Question.objects.get(id=ids[0])
    Option.objects.filter(question=q, is_correct=False).update(points=0)
    Option.objects.filter(question=q, is_correct=True).update(points=5)
    for qid in ids:
        question = Question.objects.get(id=qid)
        answer(attempt_id, token, question.number, question.options.get(is_correct=True).letter)
    data = _finish(client, attempt_id, token)
    assert data["percent"] == 100.0
    assert data["total_score"] == data["max_score"]


def test_no_duplicate_questions_in_attempt(make_attempt, imported):
    from quiz.models import Attempt

    for _ in range(5):
        attempt_id, _token = make_attempt()
        ids = Attempt.objects.get(pk=attempt_id).question_ids
        assert len(ids) == len(set(ids))
