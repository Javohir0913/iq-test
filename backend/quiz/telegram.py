"""Telegram Mini App `initData` ni bot token bilan tekshirish.

https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
"""

import hashlib
import hmac
import html
import json
import logging
import threading
import time
import urllib.request
from pathlib import Path
from urllib.parse import parse_qsl

from django.conf import settings
from django.core.cache import cache

BASE_DIR = Path(__file__).resolve().parent


class TelegramAuthError(Exception):
    pass


def validate_init_data(init_data, bot_token=None, max_age=None, now=None):
    bot_token = bot_token if bot_token is not None else settings.TELEGRAM_BOT_TOKEN
    max_age = max_age if max_age is not None else settings.TELEGRAM_AUTH_MAX_AGE
    if not bot_token:
        raise TelegramAuthError("Telegram bot token sozlanmagan")
    if not init_data:
        raise TelegramAuthError("initData bo‘sh")

    pairs = dict(parse_qsl(init_data, keep_blank_values=True, strict_parsing=False))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise TelegramAuthError("hash yo‘q")

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calculated = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated, received_hash):
        raise TelegramAuthError("imzo noto‘g‘ri")

    try:
        auth_date = int(pairs.get("auth_date", "0"))
    except ValueError as exc:
        raise TelegramAuthError("auth_date noto‘g‘ri") from exc
    now = now if now is not None else time.time()
    if max_age and now - auth_date > max_age:
        raise TelegramAuthError("initData eskirgan")

    try:
        user = json.loads(pairs.get("user", "{}"))
    except json.JSONDecodeError as exc:
        raise TelegramAuthError("user maydoni noto‘g‘ri") from exc
    if not isinstance(user, dict) or "id" not in user:
        raise TelegramAuthError("foydalanuvchi ma’lumoti yo‘q")
    return user


def sign_init_data(fields, bot_token):
    """Testlar uchun: maydonlardan imzolangan initData satrini yasaydi."""
    from urllib.parse import urlencode

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode({**fields, "hash": signature})


# --- Bot API (natija xabari, bot ma’lumoti) ---------------------------------------

logger = logging.getLogger(__name__)


def bot_api(method, payload=None, timeout=8):
    token = settings.TELEGRAM_BOT_TOKEN
    if not token:
        return None
    req = urllib.request.Request(
        f"{settings.TELEGRAM_API_BASE}/bot{token}/{method}",
        data=json.dumps(payload or {}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode())
    if not data.get("ok"):
        raise TelegramAuthError(data.get("description", "Bot API xatosi"))
    return data["result"]


def bot_username():
    """Bot username (getMe) – 1 soat keshlanadi. Token bo‘lmasa yoki xato bo‘lsa ''."""
    if settings.TELEGRAM_BOT_USERNAME:
        return settings.TELEGRAM_BOT_USERNAME.lstrip("@")
    if not settings.TELEGRAM_BOT_TOKEN:
        return ""
    cached = cache.get("tg_bot_username")
    if cached is not None:
        return cached
    try:
        username = bot_api("getMe", timeout=4).get("username", "")
    except Exception as exc:  # tarmoq xatosi sayt ishiga ta’sir qilmasin
        logger.warning("getMe xatosi: %s", exc)
        cache.set("tg_bot_username", "", 60)
        return ""
    cache.set("tg_bot_username", username, 3600)
    return username


def public_url():
    """Mini App uchun HTTPS manzil: PUBLIC_URL (https bo‘lsa) yoki Cloudflare tunnel manzili. Topilmasa ''."""
    if settings.PUBLIC_URL.startswith("https://"):
        return settings.PUBLIC_URL
    if not settings.TUNNEL_METRICS_URL:
        return ""
    cached = cache.get("tunnel_public_url")
    if cached is not None:
        return cached
    url = ""
    try:
        with urllib.request.urlopen(f"{settings.TUNNEL_METRICS_URL}/quicktunnel", timeout=2) as resp:
            host = json.loads(resp.read().decode()).get("hostname", "")
        url = f"https://{host}" if host else ""
    except Exception:
        pass
    cache.set("tunnel_public_url", url, 60)
    return url


def load_texts(lang):
    path = BASE_DIR / "i18n" / f"{lang if lang in ('uz', 'ru', 'en') else 'uz'}.json"
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)["telegram"]


def result_message(result, token, lang):
    t = load_texts(lang)
    level = result.get("level") or {}
    text = t["result"].format(
        name=html.escape(result["full_name"]),
        score=result["total_score"],
        max=result["max_score"],
        percent=round(result["percent"]),
        level=html.escape(level.get(f"name_{lang}", "—")),
    )
    stage = result.get("stage")
    if stage:
        text = t["stage_line"].format(stage=stage["number"]) + "\n" + text
        if not result.get("certificate_available"):
            text += "\n\n" + t["no_certificate"]
    keyboard = []
    base = public_url()
    if base:
        url = f"{base}/result/{result['attempt_id']}?t={token}"
        keyboard.append([{"text": t["open_result"], "web_app": {"url": url}}])
        keyboard.append([{"text": t["retake"], "web_app": {"url": f"{base}/start?lang={lang}"}}])
    payload = {"text": text, "parse_mode": "HTML"}
    if keyboard:
        payload["reply_markup"] = {"inline_keyboard": keyboard}
    return payload


def notify_result(attempt):
    """Telegram orqali kirgan ishtirokchiga natijani bot chatiga yuboradi (fon oqimida)."""
    participant = attempt.participant
    if not (settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_NOTIFY_RESULTS and participant.telegram_id):
        return
    from .services import result_payload

    lang = participant.language if participant.language in ("uz", "ru", "en") else "uz"
    payload = {"chat_id": participant.telegram_id, **result_message(result_payload(attempt), attempt.token, lang)}

    def send():
        try:
            bot_api("sendMessage", payload)
        except Exception as exc:
            logger.warning("Natija xabarini yuborib bo‘lmadi (%s): %s", participant.telegram_id, exc)

    threading.Thread(target=send, daemon=True).start()
