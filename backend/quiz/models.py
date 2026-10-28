import secrets
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

LETTERS = ["A", "B", "C", "D", "E", "F"]
MIN_POINTS = 3
MAX_POINTS = 7


class Category(models.TextChoices):
    NUMERIC = "numeric", "Sonli mantiq"
    PATTERN = "pattern", "Naqsh va ketma-ketlik"
    SPATIAL = "spatial", "Fazoviy tasavvur"


CATEGORY_NAMES = {
    "numeric": {"uz": "Sonli mantiq", "ru": "Числовая логика", "en": "Numerical logic"},
    "pattern": {"uz": "Naqsh va ketma-ketlik", "ru": "Закономерности", "en": "Patterns and sequences"},
    "spatial": {"uz": "Fazoviy tasavvur", "ru": "Пространственное мышление", "en": "Spatial reasoning"},
}


class Language(models.TextChoices):
    UZ = "uz", "O‘zbekcha"
    RU = "ru", "Русский"
    EN = "en", "English"


LANG_CODES = [code for code, _ in Language.choices]


class Difficulty(models.IntegerChoices):
    EASY = 1, "Oson"
    MEDIUM = 2, "O‘rta"
    HARD = 3, "Qiyin"


def question_upload_to(instance, filename):
    return f"questions/q{instance.number:02d}/{filename}"


def option_upload_to(instance, filename):
    return f"questions/q{instance.question.number:02d}/{filename}"


class Question(models.Model):
    class Type(models.TextChoices):
        NUMBER = "number", "Son"
        IMAGE = "image", "Rasm"

    number = models.PositiveSmallIntegerField("raqam", unique=True)
    type = models.CharField("turi", max_length=10, choices=Type.choices)
    category = models.CharField("kategoriya", max_length=10, choices=Category.choices)
    prompt_uz = models.CharField("savol (uz)", max_length=255)
    prompt_ru = models.CharField("savol (ru)", max_length=255)
    prompt_en = models.CharField("savol (en)", max_length=255, blank=True)
    figure = models.FileField("rasm", upload_to=question_upload_to, max_length=255)
    logic_uz = models.TextField("mantiq (uz)", blank=True)
    logic_ru = models.TextField("mantiq (ru)", blank=True)
    difficulty = models.PositiveSmallIntegerField(
        "qiyinlik", choices=Difficulty.choices, default=Difficulty.MEDIUM,
        help_text="Bosqich savollari shu bo‘yicha tanlanadi (bosqichdagi «maks. qiyinlik»).",
    )
    order = models.PositiveSmallIntegerField("tartib", default=0)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        ordering = ["order", "number"]
        verbose_name = "savol"
        verbose_name_plural = "savollar"

    def __str__(self):
        return f"{self.number}-savol"

    def clean_options(self, options):
        """Variantlar to‘plamini tekshiradi: 6 ta, A–F, ball 3–7, aniq bitta 7."""
        letters = sorted(o.letter for o in options)
        if letters != LETTERS:
            raise ValidationError("Savolda aniq 6 ta variant (A–F) bo‘lishi kerak.")
        for o in options:
            if not MIN_POINTS <= o.points <= MAX_POINTS:
                raise ValidationError(f"{o.letter} variant bali 3–7 oralig‘ida bo‘lishi kerak.")
        if sum(1 for o in options if o.points == MAX_POINTS) != 1:
            raise ValidationError("Savolda aniq bitta 7 ballik variant bo‘lishi kerak.")

    def clean(self):
        if self.pk:
            options = list(self.options.all())
            if options:
                self.clean_options(options)


class Option(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options", verbose_name="savol")
    letter = models.CharField("harf", max_length=1, choices=[(x, x) for x in LETTERS])
    value = models.IntegerField("son", null=True, blank=True)
    image = models.FileField("rasm", upload_to=option_upload_to, null=True, blank=True, max_length=255)
    points = models.PositiveSmallIntegerField(
        "ball", validators=[MinValueValidator(MIN_POINTS), MaxValueValidator(MAX_POINTS)]
    )
    reason_uz = models.CharField("izoh (uz)", max_length=255, blank=True)

    class Meta:
        ordering = ["question", "letter"]
        verbose_name = "variant"
        verbose_name_plural = "variantlar"
        constraints = [
            models.UniqueConstraint(fields=["question", "letter"], name="option_unique_letter"),
            models.CheckConstraint(
                condition=Q(points__gte=MIN_POINTS) & Q(points__lte=MAX_POINTS), name="option_points_3_7"
            ),
            # Bitta savolda 7 ballik variant ko‘pi bilan bitta; "kamida bitta" clean() va importda tekshiriladi.
            models.UniqueConstraint(
                fields=["question"], condition=Q(points=MAX_POINTS), name="option_single_max_points"
            ),
            models.CheckConstraint(condition=Q(letter__in=LETTERS), name="option_letter_a_f"),
        ]

    def __str__(self):
        return f"{self.question.number}{self.letter}"


class Participant(models.Model):
    full_name = models.CharField("ism familiya", max_length=120)
    phone = models.CharField("telefon", max_length=20, blank=True)
    telegram_id = models.BigIntegerField("Telegram ID", null=True, blank=True, db_index=True)
    language = models.CharField("til", max_length=2, choices=Language.choices, default=Language.UZ)
    created_at = models.DateTimeField("yaratilgan", auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "ishtirokchi"
        verbose_name_plural = "ishtirokchilar"

    def __str__(self):
        return self.full_name


class ScoreLevel(models.Model):
    """Natija darajasi – foiz (0–100) oralig‘i bo‘yicha, savollar soniga bog‘liq emas."""

    min_percent = models.PositiveSmallIntegerField("min foiz", validators=[MaxValueValidator(100)])
    max_percent = models.PositiveSmallIntegerField("max foiz", validators=[MaxValueValidator(100)])
    name_uz = models.CharField("nomi (uz)", max_length=60)
    name_ru = models.CharField("nomi (ru)", max_length=60)
    name_en = models.CharField("nomi (en)", max_length=60, blank=True)
    description_uz = models.TextField("tavsif (uz)", blank=True)
    description_ru = models.TextField("tavsif (ru)", blank=True)
    description_en = models.TextField("tavsif (en)", blank=True)

    class Meta:
        ordering = ["min_percent"]
        verbose_name = "daraja"
        verbose_name_plural = "darajalar"
        constraints = [
            models.CheckConstraint(condition=Q(min_percent__lte=models.F("max_percent")), name="level_min_lte_max"),
        ]

    def __str__(self):
        return f"{self.name_uz} ({self.min_percent}–{self.max_percent}%)"

    def clean(self):
        if self.min_percent is None or self.max_percent is None:
            return
        if self.min_percent > self.max_percent:
            raise ValidationError("Min foiz max foizdan katta bo‘lishi mumkin emas.")
        overlap = ScoreLevel.objects.exclude(pk=self.pk).filter(
            min_percent__lte=self.max_percent, max_percent__gte=self.min_percent
        )
        if overlap.exists():
            raise ValidationError(f"Oraliq boshqa daraja bilan kesishadi: {overlap.first()}")

    @classmethod
    def for_percent(cls, percent):
        # Eng katta min_percent <= foiz bo‘lgan daraja (masalan 92.9% < 93 → "Juda yuqori")
        return cls.objects.filter(min_percent__lte=percent or 0).order_by("-min_percent").first()

    def names(self):
        return {"uz": self.name_uz, "ru": self.name_ru, "en": self.name_en or self.name_uz}

    def descriptions(self):
        return {"uz": self.description_uz, "ru": self.description_ru, "en": self.description_en or self.description_uz}


class TestSettings(models.Model):
    """Yagona yozuv (singleton): admin panelda tahrirlanadigan test sozlamalari."""

    duration_minutes = models.PositiveSmallIntegerField(
        "test vaqti (daqiqa)",
        validators=[MinValueValidator(1), MaxValueValidator(300)],
        help_text="Eski (bosqichsiz) urinishlar uchun. Bosqichlar vaqti «Bosqichlar» bo‘limida.",
    )
    subscription_required = models.BooleanField(
        "kanalga obuna majburiy",
        default=False,
        help_text="Yoqilsa, test boshlash uchun barcha faol majburiy kanallarga a’zo bo‘lish kerak. "
        "Bot har bir kanalda administrator bo‘lishi shart.",
    )

    class Meta:
        verbose_name = "test sozlamalari"
        verbose_name_plural = "test sozlamalari"

    def __str__(self):
        return f"Test vaqti: {self.duration_minutes} daqiqa"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1, defaults={"duration_minutes": settings.TEST_DURATION_MINUTES})
        return obj


class Stage(models.Model):
    """Test bosqichi: savollar soni, vaqt, ochilish sharti (taklif qilingan do‘stlar) va sertifikat."""

    number = models.PositiveSmallIntegerField("bosqich", unique=True)
    question_count = models.PositiveSmallIntegerField(
        "savollar soni", validators=[MinValueValidator(1), MaxValueValidator(200)]
    )
    duration_minutes = models.PositiveSmallIntegerField(
        "vaqt (daqiqa)", validators=[MinValueValidator(1), MaxValueValidator(300)]
    )
    max_difficulty = models.PositiveSmallIntegerField(
        "maks. qiyinlik",
        choices=Difficulty.choices,
        help_text="Savollar shu qiyinlikkacha bo‘lganlar orasidan tasodifiy tanlanadi.",
    )
    friends_required = models.PositiveSmallIntegerField("taklif qilinishi kerak bo‘lgan do‘stlar", default=0)
    certificate = models.BooleanField("sertifikat beriladi", default=False)
    is_active = models.BooleanField("faol", default=True)

    class Meta:
        ordering = ["number"]
        verbose_name = "bosqich"
        verbose_name_plural = "bosqichlar"

    def __str__(self):
        return f"{self.number}-bosqich ({self.question_count} savol)"


def normalize_chat(raw):
    """Kanal identifikatori: "@username", "https://t.me/username" yoki "-100…" ID → "@username" / "-100…"."""
    value = (raw or "").strip()
    for prefix in ("https://t.me/", "http://t.me/", "t.me/"):
        if value.lower().startswith(prefix):
            value = value[len(prefix):].split("/")[0].split("?")[0]
            break
    if not value:
        return ""
    if value.lstrip("-").isdigit():
        return value
    return "@" + value.lstrip("@")


class RequiredChannel(models.Model):
    """Majburiy obuna kanali. Bot kanalda administrator bo‘lishi kerak (a’zolikni tekshirish uchun)."""

    chat = models.CharField(
        "kanal (@username yoki ID)",
        max_length=100,
        unique=True,
        help_text="Masalan: @mening_kanalim yoki -1001234567890",
    )
    title = models.CharField("nomi", max_length=120)
    invite_link = models.URLField(
        "havola", blank=True, help_text="Yopiq kanal uchun taklif havolasi. Bo‘sh bo‘lsa @username dan yasaladi."
    )
    is_active = models.BooleanField("faol", default=True)
    order = models.PositiveSmallIntegerField("tartib", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "majburiy kanal"
        verbose_name_plural = "majburiy kanallar"

    def __str__(self):
        return f"{self.title} ({self.chat})"

    def clean(self):
        self.chat = normalize_chat(self.chat)
        if not self.chat:
            raise ValidationError({"chat": "Kanal @username yoki ID sini kiriting."})

    def save(self, *args, **kwargs):
        self.chat = normalize_chat(self.chat)
        super().save(*args, **kwargs)

    @property
    def url(self):
        if self.invite_link:
            return self.invite_link
        return f"https://t.me/{self.chat[1:]}" if self.chat.startswith("@") else ""


def generate_token():
    return secrets.token_urlsafe(32)


# O‘qishda adashtiradigan belgilar (0/O, 1/I/L) yo‘q
VERIFY_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"


def generate_verify_code():
    """Sertifikat tekshiruv kodi: 10 belgi, masalan K7M2QX9P4T (ko‘rsatishda K7M2-QX9P-4T)."""
    return "".join(secrets.choice(VERIFY_ALPHABET) for _ in range(10))


def format_verify_code(code):
    return f"{code[:4]}-{code[4:8]}-{code[8:]}" if code else ""


def normalize_verify_code(raw):
    return "".join(ch for ch in (raw or "").upper() if ch.isalnum())


class Attempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "Jarayonda"
        FINISHED = "finished", "Yakunlangan"
        EXPIRED = "expired", "Vaqti tugagan"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    participant = models.ForeignKey(
        Participant, on_delete=models.CASCADE, related_name="attempts", verbose_name="ishtirokchi"
    )
    token = models.CharField(max_length=64, default=generate_token, editable=False)
    # Sertifikatdagi QR kod orqali ochiq tekshirish uchun (token emas – natijaga kirish huquqini bermaydi)
    verify_code = models.CharField(
        "tekshiruv kodi", max_length=16, unique=True, default=generate_verify_code, editable=False
    )
    status = models.CharField("holat", max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    # null – bosqichlardan oldingi (to‘liq) test
    stage = models.ForeignKey(
        Stage, on_delete=models.PROTECT, null=True, blank=True, related_name="attempts", verbose_name="bosqich"
    )
    # Shu urinishga tushgan savollar (Question.id), ko‘rsatish tartibida
    question_ids = models.JSONField("savollar", default=list, blank=True)
    started_at = models.DateTimeField("boshlangan", auto_now_add=True)
    expires_at = models.DateTimeField("muddati")
    finished_at = models.DateTimeField("tugagan", null=True, blank=True)
    total_score = models.PositiveSmallIntegerField("ball", null=True, blank=True)
    percent = models.DecimalField("foiz", max_digits=5, decimal_places=1, null=True, blank=True)
    level = models.ForeignKey(
        ScoreLevel, on_delete=models.SET_NULL, null=True, blank=True, related_name="attempts", verbose_name="daraja"
    )
    category_scores = models.JSONField("kategoriyalar", default=dict, blank=True)

    class Meta:
        ordering = ["-started_at"]
        verbose_name = "urinish"
        verbose_name_plural = "urinishlar"
        indexes = [models.Index(fields=["status", "started_at"])]

    def __str__(self):
        return f"{self.participant} · {self.started_at:%Y-%m-%d %H:%M}"

    @property
    def is_open(self):
        return self.status == self.Status.IN_PROGRESS

    @property
    def has_certificate(self):
        """Sertifikat faqat sertifikatli bosqichda (yoki bosqichlardan oldingi to‘liq testda) beriladi."""
        return self.stage is None or self.stage.certificate


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers", verbose_name="urinish")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers", verbose_name="savol")
    option = models.ForeignKey(Option, on_delete=models.CASCADE, related_name="answers", verbose_name="variant")
    answered_at = models.DateTimeField("vaqt", auto_now=True)

    class Meta:
        ordering = ["question__order", "question__number"]
        verbose_name = "javob"
        verbose_name_plural = "javoblar"
        constraints = [
            models.UniqueConstraint(fields=["attempt", "question"], name="answer_unique_per_question"),
        ]

    def __str__(self):
        return f"{self.question.number} → {self.option.letter}"

    def clean(self):
        if self.option_id and self.question_id and self.option.question_id != self.question_id:
            raise ValidationError("Variant boshqa savolga tegishli.")


class TelegramAccount(models.Model):
    """Telegram orqali kirgan foydalanuvchi (veb Login Widget yoki Mini App)."""

    telegram_id = models.BigIntegerField("Telegram ID", unique=True)
    first_name = models.CharField("ism", max_length=120, blank=True)
    last_name = models.CharField("familiya", max_length=120, blank=True)
    username = models.CharField("username", max_length=64, blank=True)
    photo_url = models.URLField("rasm", max_length=500, blank=True)
    language_code = models.CharField("til kodi", max_length=12, blank=True)
    # Natija va sertifikatdagi ism: birinchi testda kiritiladi, keyin faqat admin o‘zgartiradi
    real_name = models.CharField(
        "ism familiya (sertifikat uchun)",
        max_length=120,
        blank=True,
        help_text="Birinchi testda foydalanuvchi kiritadi; keyin faqat shu yerda o‘zgartiriladi.",
    )
    # Botda tanlangan til (bo‘sh – Telegram tilidan aniqlanadi)
    bot_language = models.CharField("bot tili", max_length=2, choices=Language.choices, blank=True)
    # Referal: kim taklif qilgan (faqat botga birinchi marta havola orqali kirganda yoziladi)
    referred_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="referrals",
        verbose_name="taklif qilgan",
    )
    # Taklif hisoblangan vaqt: do‘st majburiy kanallarga a’zo bo‘lgach (obuna o‘chiq bo‘lsa – darhol)
    referral_confirmed_at = models.DateTimeField("taklif tasdiqlangan", null=True, blank=True)
    created_at = models.DateTimeField("ro‘yxatdan o‘tgan", auto_now_add=True)
    last_login = models.DateTimeField("oxirgi kirish", null=True, blank=True)

    class Meta:
        ordering = ["-last_login"]
        verbose_name = "Telegram foydalanuvchi"
        verbose_name_plural = "Telegram foydalanuvchilar"

    def __str__(self):
        return self.real_name or self.full_name or (f"@{self.username}" if self.username else str(self.telegram_id))

    @property
    def full_name(self):
        return " ".join(filter(None, [self.first_name, self.last_name])).strip()
