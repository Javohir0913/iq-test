from django.db import migrations

DEFAULT_LEVELS = [
    (
        0,
        139,
        "Boshlang‘ich",
        "Начальный",
        "Mantiqiy fikrlash endi shakllanmoqda. Naqsh va ketma-ketliklarni muntazam yechish natijani tez oshiradi.",
        "Логическое мышление только формируется. Регулярная практика с закономерностями быстро улучшит результат.",
    ),
    (
        140,
        174,
        "O‘rta",
        "Средний",
        "Asosiy qonuniyatlarni ilg‘ay olasiz. Murakkab, ko‘p bosqichli vazifalarda e’tiborni kuchaytirish foydali.",
        "Вы улавливаете основные закономерности. Стоит уделить внимание сложным многошаговым задачам.",
    ),
    (
        175,
        209,
        "Yuqori",
        "Высокий",
        "Mantiqiy va fazoviy fikrlashingiz yaxshi rivojlangan. Ko‘pchilik vazifalarni ishonch bilan yechasiz.",
        "Логическое и пространственное мышление хорошо развиты. Вы уверенно решаете большинство задач.",
    ),
    (
        210,
        234,
        "Juda yuqori",
        "Очень высокий",
        "Murakkab qonuniyatlarni tez va aniq topasiz. Bu juda kuchli natija.",
        "Вы быстро и точно находите сложные закономерности. Это очень сильный результат.",
    ),
    (
        235,
        245,
        "A’lo",
        "Превосходный",
        "Deyarli barcha vazifalar mukammal yechilgan. Ajoyib mantiqiy fikrlash!",
        "Почти все задачи решены безупречно. Превосходное логическое мышление!",
    ),
]


def create_levels(apps, schema_editor):
    ScoreLevel = apps.get_model("quiz", "ScoreLevel")
    if ScoreLevel.objects.exists():
        return
    for mn, mx, name_uz, name_ru, desc_uz, desc_ru in DEFAULT_LEVELS:
        ScoreLevel.objects.create(
            min_score=mn,
            max_score=mx,
            name_uz=name_uz,
            name_ru=name_ru,
            description_uz=desc_uz,
            description_ru=desc_ru,
        )


def remove_levels(apps, schema_editor):
    apps.get_model("quiz", "ScoreLevel").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("quiz", "0001_initial")]

    operations = [migrations.RunPython(create_levels, remove_levels)]
