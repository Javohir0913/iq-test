"""Ballash va urinish holatini boshqarish. Barcha hisob-kitob faqat shu yerda (serverda)."""

import random
from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction
from django.db.models import Avg, Max, Min
from django.utils import timezone

from .models import (
    CATEGORY_NAMES,
    MAX_POINTS,
    MIN_POINTS,
    Answer,
    Attempt,
    Category,
    Option,
    Question,
    ScoreLevel,
    Stage,
    TestSettings,
    format_verify_code,
)


def active_questions():
    return Question.objects.filter(is_active=True).order_by("order", "number")


def active_stages():
    return Stage.objects.filter(is_active=True).order_by("number")


def pick_questions(stage, rng=random):
    """Bosqich uchun tasodifiy savollar: har qiyinlikdan sozlangan soncha.

    Biror qiyinlikda savol yetmasa – kamchilik qolgan savollardan (eng yaqin qiyinlikdan) to‘ldiriladi.
    """
    pool = {}
    for qid, diff in active_questions().values_list("id", "difficulty"):
        pool.setdefault(diff, []).append(qid)
    chosen, shortfall = [], []
    for diff, wanted in stage.difficulty_counts().items():
        available = pool.get(diff, [])
        take = rng.sample(available, min(wanted, len(available)))
        chosen += take
        taken = set(take)
        pool[diff] = [qid for qid in available if qid not in taken]
        if wanted > len(take):
            shortfall.append((diff, wanted - len(take)))
    for diff, missing in shortfall:
        for other in sorted(pool, key=lambda d: (abs(d - diff), -d)):
            if missing <= 0:
                break
            take = rng.sample(pool[other], min(missing, len(pool[other])))
            chosen += take
            taken = set(take)
            pool[other] = [qid for qid in pool[other] if qid not in taken]
            missing -= len(take)
    rng.shuffle(chosen)
    return chosen


def attempt_questions(attempt):
    """Urinishga tushgan savollar – ko‘rsatish tartibida (bazadan o‘chirilganlari tushib qoladi)."""
    ids = attempt.question_ids or []
    by_id = Question.objects.in_bulk(ids)
    return [by_id[qid] for qid in ids if qid in by_id]


def score_bounds(question_count):
    """(eng past to‘liq ball, maksimum): masalan 20 savol uchun (60, 140)."""
    return question_count * MIN_POINTS, question_count * MAX_POINTS


def compute_percent(score, question_count):
    floor, top = score_bounds(question_count)
    return percent_in_range(score, floor, top)


def percent_in_range(score, floor, top):
    """(ball − eng past) / (maksimum − eng past) × 100, 0–100 oralig‘ida."""
    score, floor, top = Decimal(score), Decimal(floor), Decimal(top)
    if top <= floor or score <= floor:
        return Decimal("0.0")
    value = (score - floor) * 100 / (top - floor)
    return min(value, Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def difficulty_weights():
    return TestSettings.load().weights()


def to_int(value):
    return int(Decimal(value).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _num(value):
    """JSON uchun: butun bo‘lsa int, aks holda 1 xonali float."""
    value = Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return int(value) if value == value.to_integral_value() else float(value)


def score_range(questions, weights=None):
    """(eng past, maksimum) ball – koeffitsientlar bilan.

    Har savol uchun: eng past = variantlardagi eng kichik ball × koeffitsient,
    maksimum = eng yuqori (to‘g‘ri javob) ball × koeffitsient.
    """
    weights = weights if weights is not None else difficulty_weights()
    bounds = option_bounds([q.id for q in questions])
    floor = top = Decimal(0)
    for q in questions:
        w = weights.get(q.difficulty, Decimal(1))
        low, high = bounds.get(q.id, (MIN_POINTS, MAX_POINTS))
        floor += Decimal(low) * w
        top += Decimal(high) * w
    return floor, top


def option_bounds(question_ids):
    """{savol_id: (eng kichik ball, eng katta ball)}."""
    return {
        row["question_id"]: (row["low"], row["high"])
        for row in Option.objects.filter(question_id__in=question_ids)
        .values("question_id")
        .annotate(low=Min("points"), high=Max("points"))
    }


def stage_max_score(stage, bank_size=None, weights=None):
    """Bosqichning maksimal bali (boshlashdan oldin ko‘rsatish uchun)."""
    weights = weights if weights is not None else difficulty_weights()
    # Har qiyinlik uchun o‘rtacha maksimal (to‘g‘ri javob) ball – savollarda ball pasaytirilgan bo‘lsa ham to‘g‘ri chiqadi
    avg_top = dict(
        Option.objects.filter(question__is_active=True, is_correct=True)
        .values("question__difficulty")
        .annotate(a=Avg("points"))
        .values_list("question__difficulty", "a")
    )
    total = sum(
        Decimal(str(avg_top.get(d) or MAX_POINTS)) * weights[d] * n for d, n in stage.difficulty_counts().items()
    )
    if bank_size is not None and stage.question_count > bank_size and stage.question_count:
        total = total * bank_size / stage.question_count
    return to_int(total)


def compute_scores(attempt):
    """Urinish uchun umumiy ball va kategoriyalar bo‘yicha ballarni hisoblaydi.

    Javobsiz savol 0 ball. Faqat urinishga tushgan savollar hisobga olinadi.
    """
    questions = attempt_questions(attempt)
    question_ids = {q.id for q in questions}
    weights = difficulty_weights()
    points_by_question = {
        a.question_id: a.option.points
        for a in Answer.objects.filter(attempt=attempt, question_id__in=question_ids).select_related("option")
    }
    bounds = option_bounds(question_ids)

    categories = {}
    for key in Category.values:
        categories[key] = {"score": 0, "max": 0, "count": 0, "answered": 0}
    total = 0
    for q in questions:
        cat = categories.setdefault(q.category, {"score": 0, "max": 0, "count": 0, "answered": 0})
        w = weights.get(q.difficulty, Decimal(1))
        pts = Decimal(points_by_question.get(q.id, 0)) * w
        cat["score"] += pts
        cat["max"] += Decimal(bounds.get(q.id, (MIN_POINTS, MAX_POINTS))[1]) * w
        cat["count"] += 1
        if q.id in points_by_question:
            cat["answered"] += 1
        total += pts

    for cat in categories.values():
        cat["percent"] = round(float(cat["score"] * 100 / cat["max"]), 1) if cat["max"] else 0.0
        cat["score"] = _num(cat["score"])
        cat["max"] = _num(cat["max"])

    return total, categories, len(questions), len(points_by_question)


def create_attempt(participant, stage):
    now = timezone.now()
    return Attempt.objects.create(
        participant=participant,
        stage=stage,
        question_ids=pick_questions(stage),
        expires_at=now + timedelta(minutes=stage.duration_minutes),
    )


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
    floor, top = score_range(attempt_questions(attempt))
    now = timezone.now()
    attempt.status = status
    attempt.finished_at = min(now, attempt.expires_at) if status == Attempt.Status.EXPIRED else now
    attempt.total_score = to_int(total)
    attempt.max_score = to_int(top)
    attempt.percent = percent_in_range(total, floor, top)
    attempt.level = ScoreLevel.for_percent(attempt.percent)
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


def attempt_max_score(attempt):
    if attempt.max_score is not None:
        return attempt.max_score
    return to_int(score_range(attempt_questions(attempt))[1])


def level_payload(level, full=False):
    if level is None:
        return None
    names = level.names()
    data = {f"name_{code}": name for code, name in names.items()}
    if full:
        data.update({f"description_{code}": text for code, text in level.descriptions().items()})
        data.update({"min_percent": level.min_percent, "max_percent": level.max_percent})
    return data


def stage_payload(attempt):
    stage = attempt.stage
    return {"number": stage.number, "certificate": stage.certificate} if stage else None


def result_payload(attempt):
    questions_count = len(attempt.question_ids or [])
    answered = attempt.answers.filter(question_id__in=attempt.question_ids or []).count()
    end = attempt.finished_at or timezone.now()
    categories = []
    for key, names in CATEGORY_NAMES.items():
        data = (attempt.category_scores or {}).get(key)
        if not data or not data.get("count", 1):
            continue
        categories.append(
            {
                "key": key,
                **{f"name_{code}": name for code, name in names.items()},
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
        "max_score": attempt_max_score(attempt),
        "percent": float(attempt.percent or 0),
        "level": level_payload(attempt.level, full=True),
        "categories": categories,
        "answered_count": answered,
        "total_questions": questions_count,
        "stage": stage_payload(attempt),
        "certificate_available": attempt.has_certificate,
        "verify_code": format_verify_code(attempt.verify_code) if attempt.has_certificate else "",
    }
