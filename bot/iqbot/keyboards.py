"""Inline klaviaturalar: Mini App (web_app) tugmalari. `base` – HTTPS manzil yoki bo‘sh satr (Mini App yo‘q)."""

from urllib.parse import quote

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from .texts import LANGS, format_date, t

LANG_NAMES = {"uz": "🇺🇿 O‘zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}


def webapp_button(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


def footer_rows(lang: str) -> list[list[InlineKeyboardButton]]:
    return [
        [
            InlineKeyboardButton(text=t(lang, "results_button"), callback_data="results"),
            InlineKeyboardButton(text=t(lang, "help_button"), callback_data="help"),
        ],
        [InlineKeyboardButton(text=t(lang, "language_button"), callback_data="lang")],
    ]


def main_menu(base: str, lang: str, progress: dict | None = None) -> InlineKeyboardMarkup:
    """Bosh menyu: kanallar (obuna bo‘lmagan bo‘lsa) yoki bosqich tugmalari, so‘ng natijalar/yordam/til."""
    rows: list[list[InlineKeyboardButton]] = []
    progress = progress or {}
    if progress.get("subscription_required") and not progress.get("subscribed"):
        for ch in progress.get("channels", []):
            if not ch["subscribed"] and ch.get("url"):
                rows.append([InlineKeyboardButton(text=t(lang, "channel_button", title=ch["title"]), url=ch["url"])])
        rows.append([InlineKeyboardButton(text=t(lang, "check_button"), callback_data="check")])
    elif base:
        stages = progress.get("stages") or []
        if not stages:
            rows.append([webapp_button(t(lang, "start_button"), f"{base}/start?lang={lang}")])
        for s in stages:
            if s["unlocked"]:
                text = t(lang, "stage_button", n=s["number"], questions=s["question_count"])
                rows.append([webapp_button(text, f"{base}/start?lang={lang}&stage={s['number']}")])
            else:
                text = t(lang, "locked_button", n=s["number"], friends=s["missing_friends"])
                rows.append([InlineKeyboardButton(text=text, callback_data="invite")])
        if any(not s["unlocked"] for s in stages):
            rows.append([InlineKeyboardButton(text=t(lang, "invite_button"), callback_data="invite")])
    return InlineKeyboardMarkup(inline_keyboard=rows + footer_rows(lang))


def start_only(base: str, lang: str) -> InlineKeyboardMarkup | None:
    if not base:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[webapp_button(t(lang, "start_button"), f"{base}/start?lang={lang}")]])


def invite_menu(lang: str, link: str) -> InlineKeyboardMarkup:
    share = f"https://t.me/share/url?url={quote(link, safe='')}&text={quote(t(lang, 'share_text'), safe='')}"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang, "share_button"), url=share)],
            [InlineKeyboardButton(text=t(lang, "check_button"), callback_data="check")],
        ]
    )


def language_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=LANG_NAMES[code], callback_data=f"setlang:{code}")] for code in LANGS]
    )


def results_menu(base: str, lang: str, attempts: list[dict]) -> InlineKeyboardMarkup | None:
    if not base:
        return None
    rows = []
    for a in attempts:
        if a["status"] == "in_progress":
            rows.append([webapp_button(t(lang, "continue_test"), f"{base}/test/{a['attempt_id']}?t={a['token']}")])
        else:
            date = format_date(a.get("finished_at"), lang)
            url = f"{base}/result/{a['attempt_id']}?t={a['token']}"
            rows.append([webapp_button(t(lang, "open_result", date=date), url)])
    rows.append([webapp_button(t(lang, "start_button"), f"{base}/start?lang={lang}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)
