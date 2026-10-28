"""Bosqichlar, majburiy kanallar, referal, savol qiyinligi, ingliz tili; darajalar balldan foizga o‘tadi."""

import math

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

# 35 savollik eski shkala: foiz = (ball − 105) / 140 × 100
OLD_FLOOR, OLD_SPAN = 105, 140

LEVEL_EN = {
    "Boshlang‘ich": (
        "Beginner",
        "Logical thinking is still taking shape. Regular practice with patterns and sequences will quickly improve the result.",
    ),
    "O‘rta": (
        "Average",
        "You catch the main patterns. It is worth paying more attention to complex, multi-step tasks.",
    ),
    "Yuqori": (
        "High",
        "Your logical and spatial thinking is well developed. You solve most tasks with confidence.",
    ),
    "Juda yuqori": ("Very high", "You find complex patterns quickly and accurately. This is a very strong result."),
    "A’lo": ("Excellent", "Almost every task was solved flawlessly. Outstanding logical thinking!"),
}

PROMPT_EN = {
    "Savol belgisi o‘rniga qaysi son turishi kerak?": "Which number should replace the question mark?",
    "Keyingi rasm qaysi?": "Which figure comes next?",
    "To‘g‘ri javobni tanlang.": "Choose the correct answer.",
    "Yetishmayotgan bo‘lak qaysi?": "Which piece is missing?",
}

DEFAULT_STAGES = [
    # number, question_count, duration_minutes, max_difficulty, friends_required, certificate
    (1, 10, 12, 1, 0, False),
    (2, 15, 18, 2, 1, False),
    (3, 20, 25, 3, 2, True),
]


def _to_percent(score, up):
    value = max(0.0, (score - OLD_FLOOR) * 100 / OLD_SPAN)
    return min(100, math.ceil(value) if up else math.floor(value))


def forwards(apps, schema_editor):
    ScoreLevel = apps.get_model("quiz", "ScoreLevel")
    for level in ScoreLevel.objects.all():
        level.min_percent = _to_percent(level.min_percent, up=True)
        level.max_percent = _to_percent(level.max_percent, up=False)
        en = LEVEL_EN.get(level.name_uz)
        if en:
            level.name_en, level.description_en = en
        level.save()

    Question = apps.get_model("quiz", "Question")
    for q in Question.objects.all():
        q.difficulty = 1 if q.number <= 15 else 2 if q.number <= 30 else 3
        q.prompt_en = PROMPT_EN.get(q.prompt_uz, "")
        q.save(update_fields=["difficulty", "prompt_en"])

    Stage = apps.get_model("quiz", "Stage")
    if not Stage.objects.exists():
        for number, count, minutes, difficulty, friends, certificate in DEFAULT_STAGES:
            Stage.objects.create(
                number=number,
                question_count=count,
                duration_minutes=minutes,
                max_difficulty=difficulty,
                friends_required=friends,
                certificate=certificate,
            )

    # Eski urinishlar: o‘sha paytdagi barcha faol savollar (1–35)
    Attempt = apps.get_model("quiz", "Attempt")
    legacy_ids = list(
        Question.objects.filter(is_active=True, number__lte=35).order_by("order", "number").values_list("id", flat=True)
    )
    Attempt.objects.filter(stage__isnull=True).update(question_ids=legacy_ids)


class Migration(migrations.Migration):
    dependencies = [("quiz", "0005_attempt_verify_code")]

    operations = [
        # --- Savollar ---
        migrations.AddField(
            model_name="question",
            name="prompt_en",
            field=models.CharField(blank=True, max_length=255, verbose_name="savol (en)"),
        ),
        migrations.AddField(
            model_name="question",
            name="difficulty",
            field=models.PositiveSmallIntegerField(
                choices=[(1, "Oson"), (2, "O‘rta"), (3, "Qiyin")],
                default=2,
                help_text="Bosqich savollari shu bo‘yicha tanlanadi (bosqichdagi «maks. qiyinlik»).",
                verbose_name="qiyinlik",
            ),
        ),
        # --- Darajalar: ball → foiz ---
        migrations.RemoveConstraint(model_name="scorelevel", name="level_min_lte_max"),
        migrations.RenameField(model_name="scorelevel", old_name="min_score", new_name="min_percent"),
        migrations.RenameField(model_name="scorelevel", old_name="max_score", new_name="max_percent"),
        migrations.AlterField(
            model_name="scorelevel",
            name="min_percent",
            field=models.PositiveSmallIntegerField(
                validators=[django.core.validators.MaxValueValidator(100)], verbose_name="min foiz"
            ),
        ),
        migrations.AlterField(
            model_name="scorelevel",
            name="max_percent",
            field=models.PositiveSmallIntegerField(
                validators=[django.core.validators.MaxValueValidator(100)], verbose_name="max foiz"
            ),
        ),
        migrations.AlterModelOptions(
            name="scorelevel",
            options={"ordering": ["min_percent"], "verbose_name": "daraja", "verbose_name_plural": "darajalar"},
        ),
        migrations.AddField(
            model_name="scorelevel",
            name="name_en",
            field=models.CharField(blank=True, max_length=60, verbose_name="nomi (en)"),
        ),
        migrations.AddField(
            model_name="scorelevel",
            name="description_en",
            field=models.TextField(blank=True, verbose_name="tavsif (en)"),
        ),
        # --- Sozlamalar ---
        migrations.AlterField(
            model_name="testsettings",
            name="duration_minutes",
            field=models.PositiveSmallIntegerField(
                help_text="Eski (bosqichsiz) urinishlar uchun. Bosqichlar vaqti «Bosqichlar» bo‘limida.",
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(300),
                ],
                verbose_name="test vaqti (daqiqa)",
            ),
        ),
        migrations.AddField(
            model_name="testsettings",
            name="subscription_required",
            field=models.BooleanField(
                default=False,
                help_text="Yoqilsa, test boshlash uchun barcha faol majburiy kanallarga a’zo bo‘lish kerak. "
                "Bot har bir kanalda administrator bo‘lishi shart.",
                verbose_name="kanalga obuna majburiy",
            ),
        ),
        # --- Bosqichlar va kanallar ---
        migrations.CreateModel(
            name="Stage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("number", models.PositiveSmallIntegerField(unique=True, verbose_name="bosqich")),
                (
                    "question_count",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(200),
                        ],
                        verbose_name="savollar soni",
                    ),
                ),
                (
                    "duration_minutes",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(300),
                        ],
                        verbose_name="vaqt (daqiqa)",
                    ),
                ),
                (
                    "max_difficulty",
                    models.PositiveSmallIntegerField(
                        choices=[(1, "Oson"), (2, "O‘rta"), (3, "Qiyin")],
                        help_text="Savollar shu qiyinlikkacha bo‘lganlar orasidan tasodifiy tanlanadi.",
                        verbose_name="maks. qiyinlik",
                    ),
                ),
                (
                    "friends_required",
                    models.PositiveSmallIntegerField(default=0, verbose_name="taklif qilinishi kerak bo‘lgan do‘stlar"),
                ),
                ("certificate", models.BooleanField(default=False, verbose_name="sertifikat beriladi")),
                ("is_active", models.BooleanField(default=True, verbose_name="faol")),
            ],
            options={"ordering": ["number"], "verbose_name": "bosqich", "verbose_name_plural": "bosqichlar"},
        ),
        migrations.CreateModel(
            name="RequiredChannel",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "chat",
                    models.CharField(
                        help_text="Masalan: @mening_kanalim yoki -1001234567890",
                        max_length=100,
                        unique=True,
                        verbose_name="kanal (@username yoki ID)",
                    ),
                ),
                ("title", models.CharField(max_length=120, verbose_name="nomi")),
                (
                    "invite_link",
                    models.URLField(
                        blank=True,
                        help_text="Yopiq kanal uchun taklif havolasi. Bo‘sh bo‘lsa @username dan yasaladi.",
                        verbose_name="havola",
                    ),
                ),
                ("is_active", models.BooleanField(default=True, verbose_name="faol")),
                ("order", models.PositiveSmallIntegerField(default=0, verbose_name="tartib")),
            ],
            options={
                "ordering": ["order", "id"],
                "verbose_name": "majburiy kanal",
                "verbose_name_plural": "majburiy kanallar",
            },
        ),
        # --- Urinishlar ---
        migrations.AddField(
            model_name="attempt",
            name="stage",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="attempts",
                to="quiz.stage",
                verbose_name="bosqich",
            ),
        ),
        migrations.AddField(
            model_name="attempt",
            name="question_ids",
            field=models.JSONField(blank=True, default=list, verbose_name="savollar"),
        ),
        # --- Til ---
        migrations.AlterField(
            model_name="participant",
            name="language",
            field=models.CharField(
                choices=[("uz", "O‘zbekcha"), ("ru", "Русский"), ("en", "English")],
                default="uz",
                max_length=2,
                verbose_name="til",
            ),
        ),
        # --- Telegram: til va referal ---
        migrations.AddField(
            model_name="telegramaccount",
            name="bot_language",
            field=models.CharField(
                blank=True,
                choices=[("uz", "O‘zbekcha"), ("ru", "Русский"), ("en", "English")],
                max_length=2,
                verbose_name="bot tili",
            ),
        ),
        migrations.AddField(
            model_name="telegramaccount",
            name="referred_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="referrals",
                to="quiz.telegramaccount",
                verbose_name="taklif qilgan",
            ),
        ),
        migrations.AddField(
            model_name="telegramaccount",
            name="referral_confirmed_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="taklif tasdiqlangan"),
        ),
        migrations.AddConstraint(
            model_name="scorelevel",
            constraint=models.CheckConstraint(
                condition=models.Q(("min_percent__lte", models.F("max_percent"))), name="level_min_lte_max"
            ),
        ),
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]
