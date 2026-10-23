"""`.env` dagi DJANGO_SUPERUSER_* qiymatlari bo‘yicha superuser yaratadi (mavjud bo‘lsa tegmaydi)."""

import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD bo‘yicha superuser yaratadi"

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME")
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not username or not password:
            self.stdout.write("DJANGO_SUPERUSER_USERNAME/PASSWORD berilmagan — o‘tkazib yuborildi.")
            return
        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f"Superuser '{username}' mavjud.")
            return
        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' yaratildi."))
