"""Bosqichlarga kirish: majburiy kanallarga obuna, do‘st taklif qilish (referal) va bosqich ochilishi."""

import logging
import threading

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from .models import Attempt, RequiredChannel, Stage, TelegramAccount, TestSettings
from .telegram import bot_api, bot_username

logger = logging.getLogger(__name__)

MEMBER_STATUSES = {"creator", "administrator", "member"}
REFERRAL_PREFIX = "ref"


def required_channels():
    """Obuna majburiy bo‘lsa – faol kanallar, aks holda bo‘sh ro‘yxat."""
    if not TestSettings.load().subscription_required:
        return []
    return list(RequiredChannel.objects.filter(is_active=True))


def is_member(chat, telegram_id):
    """True/False – a’zo yoki yo‘q. Bot kanalni tekshira olmasa (admin emas, kanal topilmadi) – None."""
    key = f"tg_member:{chat}:{telegram_id}"
    cached = cache.get(key)
    if cached is not None:
        return cached
    try:
        member = bot_api("getChatMember", {"chat_id": chat, "user_id": telegram_id}, timeout=5)
    except Exception as exc:
        logger.warning("Kanal a’zoligini tekshirib bo‘lmadi (%s): %s", chat, exc)
        return None
    status = member.get("status")
    result = status in MEMBER_STATUSES or (status == "restricted" and bool(member.get("is_member")))
    # A’zo bo‘lsa uzoqroq, bo‘lmasa qisqa kesh – obuna bo‘lgach tez sezilsin
    cache.set(key, result, 300 if result else 15)
    return result


def channel_statuses(telegram_id, channels=None):
    channels = required_channels() if channels is None else channels
    items = []
    for ch in channels:
        member = is_member(ch.chat, telegram_id)
        items.append(
            {
                "title": ch.title,
                "url": ch.url,
                # Bot tekshira olmagan kanal foydalanuvchini to‘sib qo‘ymaydi (sozlash xatosi – logda)
                "subscribed": member is not False,
            }
        )
    return items


def is_subscribed(telegram_id, channels=None):
    return all(item["subscribed"] for item in channel_statuses(telegram_id, channels))


def referral_link(account):
    username = bot_username()
    return f"https://t.me/{username}?start={REFERRAL_PREFIX}{account.telegram_id}" if username else ""


def parse_referral(payload):
    value = (payload or "").strip()
    if not value.startswith(REFERRAL_PREFIX):
        return None
    digits = value[len(REFERRAL_PREFIX):]
    return int(digits) if digits.isdigit() else None


def confirmed_friends(account):
    return account.referrals.filter(referral_confirmed_at__isnull=False).count()


def attach_referrer(account, referrer_id):
    """Faqat yangi foydalanuvchiga (botga birinchi kirish) va o‘zini emas – referal yoziladi."""
    if not referrer_id or referrer_id == account.telegram_id or account.referred_by_id:
        return False
    referrer = TelegramAccount.objects.filter(telegram_id=referrer_id).first()
    if referrer is None:
        return False
    account.referred_by = referrer
    account.save(update_fields=["referred_by"])
    return True


def confirm_referral(account, channels=None):
    """Taklif qilingan do‘st kanallarga a’zo bo‘lsa (yoki obuna o‘chiq bo‘lsa) – taklif hisoblanadi."""
    if not account.referred_by_id or account.referral_confirmed_at:
        return False
    if not is_subscribed(account.telegram_id, channels):
        return False
    with transaction.atomic():
        updated = TelegramAccount.objects.filter(pk=account.pk, referral_confirmed_at__isnull=True).update(
            referral_confirmed_at=timezone.now()
        )
    if not updated:
        return False
    account.refresh_from_db(fields=["referral_confirmed_at"])
    _notify_referrer(account)
    return True


def _notify_referrer(friend):
    from .telegram import load_texts

    referrer = friend.referred_by
    if referrer is None:
        return
    lang = referrer.bot_language or lang_from_code(referrer.language_code)
    count = confirmed_friends(referrer)
    text = load_texts(lang)["friend_joined"].format(name=_html(str(friend)), count=count)

    def send():
        try:
            bot_api("sendMessage", {"chat_id": referrer.telegram_id, "text": text, "parse_mode": "HTML"})
        except Exception as exc:
            logger.info("Taklif xabarini yuborib bo‘lmadi (%s): %s", referrer.telegram_id, exc)

    threading.Thread(target=send, daemon=True).start()


def _html(value):
    from html import escape

    return escape(value)


def lang_from_code(language_code):
    code = (language_code or "").lower()[:2]
    if code in {"ru", "be", "uk", "kk"}:
        return "ru"
    return "uz"


def account_language(account):
    return account.bot_language or lang_from_code(account.language_code)


def progress(account):
    """Foydalanuvchining bosqichlar holati (sayt va bot uchun)."""
    channels = required_channels()
    statuses = channel_statuses(account.telegram_id, channels) if account else []
    subscribed = all(item["subscribed"] for item in statuses)
    if account and subscribed:
        confirm_referral(account, channels)
    friends = confirmed_friends(account) if account else 0
    pending = account.referrals.filter(referral_confirmed_at__isnull=True).count() if account else 0

    finished = {}
    if account:
        rows = (
            Attempt.objects.filter(participant__telegram_id=account.telegram_id, stage__isnull=False)
            .exclude(status=Attempt.Status.IN_PROGRESS)
            .values_list("stage__number", "percent")
        )
        for number, percent in rows:
            entry = finished.setdefault(number, {"count": 0, "best_percent": 0.0})
            entry["count"] += 1
            entry["best_percent"] = max(entry["best_percent"], float(percent or 0))

    stages = []
    for stage in Stage.objects.filter(is_active=True).order_by("number"):
        missing_friends = max(0, stage.friends_required - friends)
        stages.append(
            {
                "number": stage.number,
                "question_count": stage.question_count,
                "duration_minutes": stage.duration_minutes,
                "friends_required": stage.friends_required,
                "certificate": stage.certificate,
                "unlocked": subscribed and missing_friends == 0,
                "missing_friends": missing_friends,
                "finished_count": finished.get(stage.number, {}).get("count", 0),
                "best_percent": finished.get(stage.number, {}).get("best_percent"),
            }
        )
    return {
        "subscription_required": bool(channels),
        "subscribed": subscribed,
        "channels": statuses,
        "friends": friends,
        "pending_friends": pending,
        "referral_link": referral_link(account) if account else "",
        "stages": stages,
    }


def stage_access_error(account, stage):
    """Bosqichni boshlash mumkin bo‘lmasa – xato kodi, aks holda None."""
    channels = required_channels()
    if channels:
        if account is None or not is_subscribed(account.telegram_id, channels):
            return "subscription_required"
        confirm_referral(account, channels)
    if stage.friends_required:
        if account is None or confirmed_friends(account) < stage.friends_required:
            return "friends_required"
    return None
