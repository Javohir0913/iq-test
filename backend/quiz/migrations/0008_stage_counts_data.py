"""Bosqichlarning eski «maks. qiyinlik» sozlamasini oson/o‘rta/qiyin soniga o‘tkazadi.

Masalan 15 savol, maks. qiyinlik 2 → 8 oson + 7 o‘rta. Eski yakunlangan urinishlarga maks. ball yoziladi
(koeffitsient 1 bo‘lgan davrdagi: savollar × 7).
"""

from django.conf import settings
from django.db import migrations


def forwards(apps, schema_editor):
    Stage = apps.get_model("quiz", "Stage")
    TestSettings = apps.get_model("quiz", "TestSettings")
    Attempt = apps.get_model("quiz", "Attempt")

    obj, _ = TestSettings.objects.get_or_create(pk=1, defaults={"duration_minutes": settings.TEST_DURATION_MINUTES})
    for stage in Stage.objects.all():
        levels = max(1, min(3, stage.max_difficulty or 3))
        base, extra = divmod(stage.question_count or 0, levels)
        counts = [base + (1 if i < extra else 0) for i in range(levels)] + [0] * (3 - levels)
        stage.easy_count, stage.medium_count, stage.hard_count = counts
        stage.question_count = sum(counts)
        stage.settings_id = obj.pk
        stage.save(update_fields=["easy_count", "medium_count", "hard_count", "question_count", "settings"])

    # To‘g‘ri javob – shu paytgacha 7 ballik variant edi
    Option = apps.get_model("quiz", "Option")
    Option.objects.filter(points=7).update(is_correct=True)

    for attempt in Attempt.objects.filter(total_score__isnull=False, max_score__isnull=True).only("id", "question_ids"):
        attempt.max_score = len(attempt.question_ids or []) * 7
        attempt.save(update_fields=["max_score"])


class Migration(migrations.Migration):
    dependencies = [("quiz", "0007_difficulty_weights_correct_flag")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
