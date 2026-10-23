from django.db import migrations, models

import quiz.models


def fill_codes(apps, schema_editor):
    Attempt = apps.get_model("quiz", "Attempt")
    used = set()
    for attempt in Attempt.objects.filter(verify_code__isnull=True).only("pk"):
        code = quiz.models.generate_verify_code()
        while code in used:
            code = quiz.models.generate_verify_code()
        used.add(code)
        Attempt.objects.filter(pk=attempt.pk).update(verify_code=code)


class Migration(migrations.Migration):
    dependencies = [("quiz", "0004_telegram_account_real_name")]

    operations = [
        # 1) bo‘sh maydon, 2) mavjud urinishlarga noyob kod, 3) majburiy + unique
        migrations.AddField(
            model_name="attempt",
            name="verify_code",
            field=models.CharField(max_length=16, null=True, editable=False, verbose_name="tekshiruv kodi"),
        ),
        migrations.RunPython(fill_codes, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="attempt",
            name="verify_code",
            field=models.CharField(
                default=quiz.models.generate_verify_code,
                editable=False,
                max_length=16,
                unique=True,
                verbose_name="tekshiruv kodi",
            ),
        ),
    ]
