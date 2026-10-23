"""Ballash va urinish holatini boshqarish. Barcha hisob-kitob faqat shu yerda (serverda)."""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.utils import timezone

from .models import (
    CATEGORY_NAMES,
    MAX_POINTS,
    MIN_POINTS,
    Answer,
    Attempt,
    Category,
    Question,
    ScoreLevel,
    TestSettings,
    format_verify_code,
)


def active_questions():
    return Question.objects.filter(is_active=True).order_by("order", "number")


def score_bounds(question_count):
    """(eng past to‘liq ball, maksimum): 35 savol uchun (105, 245)."""
    return question_count * MIN_POINTS, question_count * MAX_POINTS


def compute_percent(score, question_count):
    floor, top = score_bounds(question_count)
    if top <= floor or score <= floor:
        return Decimal("0.0")
    value = Decimal(score - floor) * 100 / Decimal(top - floor)
    return min(value, Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def compute_scores(attempt):
    """Urinish uchun umumiy ball va kategoriyalar bo‘yicha ballarni hisoblaydi.

    Javobsiz savol 0 ball. Faqat faol savollar hisobga olinadi.
    """
    questions = list(active_questions())
    question_ids = {q.id for q in questions}
    points_by_question = {
        a.question_id: a.option.points
        for a in Answer.objects.filter(attempt=attempt, question_id__in=question_ids).select_related("option")
    }

    categories = {}
    for key in Category.values:
        categories[key] = {"score": 0, "max": 0, "count": 0, "answered": 0}
    total = 0
    for q in questions:
        cat = categories.setdefault(q.category, {"score": 0, "max": 0, "count": 0, "answered": 0})
        pts = points_by_question.get(q.id, 0)
        cat["score"] += pts
        cat["max"] += MAX_POINTS
        cat["count"] += 1
        if q.id in points_by_question:
            cat["answered"] += 1
        total += pts

    for cat in categories.values():
        cat["percent"] = round(cat["score"] * 100 / cat["max"], 1) if cat["max"] else 0.0

    return total, categories, len(questions), len(points_by_question)


def create_attempt(participant):
    duration = TestSettings.load().duration_minutes
    now = timezone.now()
    return Attempt.objects.create(participant=participant, expires_at=now + timedelta(minutes=duration))


def is_expired(attempt, now=None, grace_seconds=0):
    now = now or timezone.now()
    return now > attempt.expires_at + timedelta(seconds=grace_seconds)


@transaction.atomic
def finalize(attempt, status=Attempt.Status.FINISHED):
    """Urinishni yakunlaydi va natijani saqlaydi. Takroriy chaqiruv xavfsiz."""
    attempt = Attempt.objects.select_for_update().get(pk=attempt.pk)
    if not attempt.is_open:
        return attempt
    total, categories, count, _ = compute_scores(attempt)
    now = timezone.now()
    attempt.status = status
    attempt.finished_at = min(now, attempt.expires_at) if status == Attempt.Status.EXPIRED else now
    attempt.total_score = total
    attempt.percent = compute_percent(total, count)
    attempt.level = ScoreLevel.for_score(total)
    attempt.category_scores = categories
    attempt.save()
    transaction.on_commit(lambda: _notify(attempt))
    return attempt


def _notify(attempt):
    from .telegram import notify_result

    notify_result(attempt)


def expire_if_needed(attempt):
    if attempt.is_open and is_expired(attempt):
        return finalize(attempt, status=Attempt.Status.EXPIRED)
    return attempt


def result_payload(attempt):
    questions_count = active_questions().count()
    answered = attempt.answers.filter(question__is_active=True).count()
    level = attempt.level
    end = attempt.finished_at or timezone.now()
    categories = []
    for key, names in CATEGORY_NAMES.items():
        data = (attempt.category_scores or {}).get(key)
        if not data:
            continue
        categories.append(
            {
                "key": key,
                "name_uz": names["uz"],
                "name_ru": names["ru"],
                "score": data["score"],
                "max": data["max"],
                "percent": data["percent"],
            }
        )
    return {
        "attempt_id": str(attempt.id),
        "status": attempt.status,
        "full_name": attempt.participant.full_name,
        "language": attempt.participant.language,
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "duration_seconds": max(0, int((end - attempt.started_at).total_seconds())),
        "total_score": attempt.total_score,
        "max_score": score_bounds(questions_count)[1],
        "percent": float(attempt.percent or 0),
        "level": (
            {
                "name_uz": level.name_uz,
                "name_ru": level.name_ru,
                "description_uz": level.description_uz,
                "description_ru": level.description_ru,
                "min_score": level.min_score,
                "max_score": level.max_score,
            }
            if level
            else None
        ),
        "categories": categories,
        "answered_count": answered,
        "total_questions": questions_count,
        "verify_code": format_verify_code(attempt.verify_code),
    }
