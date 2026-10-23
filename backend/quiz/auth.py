"""Telegram orqali kirish: Login Widget (veb) va Mini App initData, imzolangan sessiya tokeni.

Login Widget tekshiruvi: https://core.telegram.org/widgets/login#checking-authorization
"""

import hashlib
import hmac
import time

from django.conf import settings
from django.core import signing
from django.utils import timezone

from .models import TelegramAccount
from .telegram import TelegramAuthError, validate_init_data

SESSION_SALT = "iq.telegram.session"
WIDGET_FIELDS = {"id", "first_name", "last_name", "username", "photo_url", "auth_date", "hash"}


def validate_widget_data(data, bot_token=None, max_age=None, now=None):
    """Login Widget ma’lumotini tekshiradi va foydalanuvchi maydonlarini qaytaradi."""
    bot_token = bot_token if bot_token is not None else settings.TELEGRAM_BOT_TOKEN
    max_age = max_age if max_age is not None else settings.TELEGRAM_AUTH_MAX_AGE
    if not bot_token:
        raise TelegramAuthError("Telegram bot token sozlanmagan")
    fields = {k: str(v) for k, v in data.items() if k in WIDGET_FIELDS and v is not None and v != ""}
    received_hash = fields.pop("hash", None)
    if not received_hash or "id" not in fields or "auth_date" not in fields:
        raise TelegramAuthError("maydonlar yetarli emas")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise TelegramAuthError("imzo noto‘g‘ri")

    now = now if now is not None else time.time()
    try:
        auth_date = int(fields["auth_date"])
    except ValueError as exc:
        raise TelegramAuthError("auth_date noto‘g‘ri") from exc
    if max_age and now - auth_date > max_age:
        raise TelegramAuthError("ma’lumot eskirgan")
    return {**fields, "id": int(fields["id"])}


def sign_widget_data(fields, bot_token):
    """Testlar uchun: Login Widget ma’lumotiga imzo qo‘shadi."""
    fields = {k: str(v) for k, v in fields.items()}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    return {**fields, "hash": hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()}


def upsert_account(user):
    defaults = {
        "first_name": user.get("first_name", "")[:120],
        "last_name": user.get("last_name", "")[:120],
        "username": user.get("username", "")[:64],
        "last_login": timezone.now(),
    }
    if user.get("photo_url"):
        defaults["photo_url"] = user["photo_url"][:500]
    if user.get("language_code"):
        defaults["language_code"] = user["language_code"][:12]
    account, _ = TelegramAccount.objects.update_or_create(telegram_id=int(user["id"]), defaults=defaults)
    return account


def account_from_init_data(init_data):
    return upsert_account(validate_init_data(init_data))


def issue_token(account):
    return signing.dumps({"tg": account.telegram_id}, salt=SESSION_SALT, compress=True)


def account_from_request(request):
    """`Authorization: Bearer <token>` dan Telegram akkauntini aniqlaydi (bo‘lmasa None)."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    try:
        data = signing.loads(header[7:].strip(), salt=SESSION_SALT, max_age=settings.AUTH_SESSION_DAYS * 86400)
    except signing.BadSignature:
        return None
    return TelegramAccount.objects.filter(telegram_id=data.get("tg")).first()


def account_payload(account):
    return {
        "telegram_id": account.telegram_id,
        "first_name": account.first_name,
        "last_name": account.last_name,
        "full_name": account.full_name,
        "username": account.username,
        "photo_url": account.photo_url,
        "language_code": account.language_code,
    }
