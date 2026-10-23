"""questions.json dan savollar, variantlar va rasmlarni bazaga import qilish.

    python manage.py import_questions /app/namunalar/questions.json [--if-empty]

Qayta ishga tushirilsa dublikat yaratmaydi: savollar `number`, variantlar (savol, harf) bo‘yicha yangilanadi.
"""

import json
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from quiz.models import LETTERS, MAX_POINTS, MIN_POINTS, Category, Option, Question


def validate_question(q):
    num = q.get("number")
    where = f"{num}-savol"
    if not isinstance(num, int) or num < 1:
        raise CommandError(f"Savol raqami noto‘g‘ri: {num!r}")
    if q.get("type") not in Question.Type.values:
        raise CommandError(f"{where}: turi noto‘g‘ri ({q.get('type')!r})")
    if q.get("category") not in Category.values:
        raise CommandError(f"{where}: kategoriya noto‘g‘ri ({q.get('category')!r})")
    prompt = q.get("prompt") or {}
    if not prompt.get("uz") or not prompt.get("ru"):
        raise CommandError(f"{where}: savol matni (uz/ru) yo‘q")
    if not q.get("figure"):
        raise CommandError(f"{where}: rasm yo‘li yo‘q")
    options = q.get("options") or []
    letters = sorted(o.get("letter") for o in options)
    if letters != LETTERS:
        raise CommandError(f"{where}: aniq 6 ta variant (A–F) bo‘lishi kerak, topildi: {letters}")
    for o in options:
        pts = o.get("points")
        if not isinstance(pts, int) or not MIN_POINTS <= pts <= MAX_POINTS:
            raise CommandError(f"{where}: {o['letter']} variant bali 3–7 oralig‘ida emas ({pts!r})")
        if q["type"] == "number" and not isinstance(o.get("value"), int):
            raise CommandError(f"{where}: {o['letter']} variantda son (value) yo‘q")
        if q["type"] == "image" and not o.get("image"):
            raise CommandError(f"{where}: {o['letter']} variantda rasm yo‘q")
    sevens = [o["letter"] for o in options if o["points"] == MAX_POINTS]
    if len(sevens) != 1:
        raise CommandError(f"{where}: aniq bitta 7 ballik variant bo‘lishi kerak, topildi: {sevens}")
    if q.get("correct") and q["correct"] != sevens[0]:
        raise CommandError(f"{where}: to‘g‘ri javob ({q['correct']}) 7 ballik variant ({sevens[0]}) bilan mos emas")


class Command(BaseCommand):
    help = "questions.json dan savollar va rasmlarni import qiladi (idempotent)"

    def add_arguments(self, parser):
        parser.add_argument("path", type=str, help="questions.json fayliga yo‘l")
        parser.add_argument(
            "--if-empty", action="store_true", help="Bazada savollar bo‘lsa, hech narsa qilmaydi (birinchi ishga tushirish)"
        )

    def handle(self, *args, path, if_empty=False, **options):
        if if_empty and Question.objects.exists():
            self.stdout.write("Savollar allaqachon mavjud — import o‘tkazib yuborildi.")
            return

        json_path = Path(path)
        if not json_path.is_file():
            raise CommandError(f"Fayl topilmadi: {json_path}")
        base_dir = json_path.parent
        try:
            data = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"JSON xato: {exc}") from exc

        questions = data.get("questions") or []
        if not questions:
            raise CommandError("Faylda savollar yo‘q")
        numbers = [q.get("number") for q in questions]
        if len(numbers) != len(set(numbers)):
            raise CommandError("Savol raqamlari takrorlangan")
        for q in questions:
            validate_question(q)
            self._check_file(base_dir, q["figure"])
            for o in q["options"]:
                if o.get("image"):
                    self._check_file(base_dir, o["image"])

        created = updated = 0
        with transaction.atomic():
            for q in questions:
                is_new = self._import_question(base_dir, q)
                created += is_new
                updated += not is_new

        self.stdout.write(self.style.SUCCESS(f"Import tugadi: {created} ta yangi, {updated} ta yangilangan savol."))

    def _check_file(self, base_dir, rel):
        if not (base_dir / rel).is_file():
            raise CommandError(f"Rasm topilmadi: {base_dir / rel}")

    def _store_file(self, base_dir, rel, number):
        """Faylni media ga deterministik nom bilan yozadi; mazmun o‘zgarmagan bo‘lsa tegmaydi."""
        src = base_dir / rel
        content = src.read_bytes()
        target = f"questions/q{number:02d}/{src.name}"
        if default_storage.exists(target):
            with default_storage.open(target, "rb") as fh:
                if fh.read() == content:
                    return target
            default_storage.delete(target)
        return default_storage.save(target, ContentFile(content))

    def _import_question(self, base_dir, q):
        number = q["number"]
        defaults = {
            "type": q["type"],
            "category": q["category"],
            "prompt_uz": q["prompt"]["uz"],
            "prompt_ru": q["prompt"]["ru"],
            "logic_uz": q.get("logic_uz", ""),
            "order": number,
        }
        if "logic_ru" in q:
            defaults["logic_ru"] = q["logic_ru"]
        question, is_new = Question.objects.update_or_create(number=number, defaults=defaults)
        question.figure.name = self._store_file(base_dir, q["figure"], number)
        question.save(update_fields=["figure"])

        # 7 ballik variant harfi o‘zgarsa, qisman unique cheklov to‘qnashmasligi uchun avval pasaytiramiz
        Option.objects.filter(question=question).update(points=MIN_POINTS)
        for o in q["options"]:
            option, _ = Option.objects.update_or_create(
                question=question,
                letter=o["letter"],
                defaults={
                    "points": o["points"],
                    "value": o.get("value"),
                    "reason_uz": o.get("reason_uz", ""),
                },
            )
            image_name = self._store_file(base_dir, o["image"], number) if o.get("image") else None
            if (option.image.name or None) != image_name:
                option.image.name = image_name
                option.save(update_fields=["image"])
        return is_new
