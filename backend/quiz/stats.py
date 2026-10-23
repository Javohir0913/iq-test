"""Admin statistikasi: jami urinishlar, o‘rtacha ball, darajalar va variantlar taqsimoti."""

from datetime import timedelta

from django.db.models import Avg, Count, F, Q
from django.db.models.functions import TruncDate
from django.utils import timezone

from .models import LETTERS, MAX_POINTS, Answer, Attempt, Option, Question, ScoreLevel


def collect_stats():
    attempts = Attempt.objects.all()
    closed = attempts.exclude(status=Attempt.Status.IN_PROGRESS)
    agg = closed.aggregate(avg_score=Avg("total_score"), avg_percent=Avg("percent"))
    durations = [
        (a["finished_at"] - a["started_at"]).total_seconds()
        for a in closed.filter(finished_at__isnull=False).values("started_at", "finished_at")[:5000]
    ]

    total_closed = closed.count()
    levels = []
    level_counts = dict(closed.values_list("level").annotate(n=Count("id")).values_list("level", "n"))
    for level in ScoreLevel.objects.all():
        n = level_counts.get(level.id, 0)
        levels.append(
            {
                "name": level.name_uz,
                "range": f"{level.min_score}–{level.max_score}",
                "count": n,
                "share": round(n * 100 / total_closed, 1) if total_closed else 0,
            }
        )

    # Har bir savol bo‘yicha variantlar necha marta tanlangani
    counts = {
        (row["question_id"], row["option__letter"]): row["n"]
        for row in Answer.objects.filter(attempt__in=closed)
        .values("question_id", "option__letter")
        .annotate(n=Count("id"))
    }
    points = {(o.question_id, o.letter): o.points for o in Option.objects.all()}
    questions = []
    for q in Question.objects.order_by("order", "number"):
        per_letter = [counts.get((q.id, letter), 0) for letter in LETTERS]
        answered = sum(per_letter)
        correct = next((c for letter, c in zip(LETTERS, per_letter) if points.get((q.id, letter)) == MAX_POINTS), 0)
        options = []
        for letter, n in zip(LETTERS, per_letter):
            options.append(
                {
                    "letter": letter,
                    "count": n,
                    "points": points.get((q.id, letter)),
                    "is_correct": points.get((q.id, letter)) == MAX_POINTS,
                    "share": round(n * 100 / answered, 1) if answered else 0,
                }
            )
        questions.append(
            {
                "number": q.number,
                "category": q.get_category_display(),
                "is_active": q.is_active,
                "answered": answered,
                "skipped": max(total_closed - answered, 0),
                "correct_rate": round(correct * 100 / answered, 1) if answered else None,
                "options": options,
            }
        )

    since = timezone.now() - timedelta(days=13)
    daily = list(
        attempts.filter(started_at__gte=since)
        .annotate(day=TruncDate("started_at"))
        .values("day")
        .annotate(n=Count("id"))
        .order_by("day")
    )
    daily_max = max((d["n"] for d in daily), default=0)
    for d in daily:
        d["height"] = round(d["n"] * 100 / daily_max) if daily_max else 0

    hardest = sorted(
        (q for q in questions if q["correct_rate"] is not None), key=lambda q: q["correct_rate"]
    )[:5]

    return {
        "total_attempts": attempts.count(),
        "finished": attempts.filter(status=Attempt.Status.FINISHED).count(),
        "expired": attempts.filter(status=Attempt.Status.EXPIRED).count(),
        "in_progress": attempts.filter(status=Attempt.Status.IN_PROGRESS).count(),
        "avg_score": round(agg["avg_score"] or 0, 1),
        "avg_percent": round(float(agg["avg_percent"] or 0), 1),
        "avg_minutes": round(sum(durations) / len(durations) / 60, 1) if durations else 0,
        "max_score": Question.objects.filter(is_active=True).count() * MAX_POINTS,
        "levels": levels,
        "questions": questions,
        "hardest": hardest,
        "daily": daily,
        "letters": LETTERS,
        "top_score": closed.order_by(F("total_score").desc(nulls_last=True)).values_list("total_score", flat=True).first(),
        "telegram_share": round(
            attempts.filter(~Q(participant__telegram_id=None)).count() * 100 / attempts.count(), 1
        )
        if attempts.exists()
        else 0,
    }


def dashboard_callback(request, context):
    context.update({"stats": collect_stats()})
    return context
