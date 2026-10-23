"""Inline klaviaturalar: Mini App (web_app) tugmalari. `base` – HTTPS manzil yoki bo‘sh satr (Mini App yo‘q)."""

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

from .texts import format_date, t


def webapp_button(text: str, url: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url))


def main_menu(base: str, lang: str) -> InlineKeyboardMarkup:
    rows = []
    if base:
        rows.append([webapp_button(t(lang, "start_button"), f"{base}/start?lang={lang}")])
    rows.append(
        [
            InlineKeyboardButton(text=t(lang, "results_button"), callback_data="results"),
            InlineKeyboardButton(text=t(lang, "help_button"), callback_data="help"),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def start_only(base: str, lang: str) -> InlineKeyboardMarkup | None:
    if not base:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[[webapp_button(t(lang, "start_button"), f"{base}/start?lang={lang}")]])


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
