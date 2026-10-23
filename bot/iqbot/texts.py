"""Bot matnlari (i18n/uz.json, i18n/ru.json) va yordamchi formatlash funksiyalari."""

import json
from datetime import datetime
from functools import lru_cache
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"
TZ = ZoneInfo("Asia/Tashkent")


@lru_cache(maxsize=4)
def texts(lang: str) -> dict:
    with open(I18N_DIR / f"{lang}.json", encoding="utf-8") as fh:
        return json.load(fh)


def lang_of(language_code: str | None) -> str:
    """Telegram tilidan bot tili: rus, belarus, ukrain, qozoq → ru; qolganlari → uz."""
    code = (language_code or "").lower()
    return "ru" if code[:2] in {"ru", "be", "uk", "kk"} else "uz"


def t(lang: str, key: str, **kwargs) -> str:
    value = texts(lang)
    for part in key.split("."):
        value = value[part]
    return value.format(**kwargs) if kwargs else value


def format_date(iso: str | None, lang: str) -> str:
    if not iso:
        return "—"
    dt = datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)
    return dt.strftime(t(lang, "date_format"))


def results_text(lang: str, data: dict) -> str:
    lines = [t(lang, "results_title"), ""]
    for a in data["attempts"]:
        date = format_date(a.get("finished_at") or a.get("started_at"), lang)
        if a["status"] == "in_progress":
            lines.append(t(lang, "in_progress_line", date=date))
            continue
        level = (a.get("level") or {}).get(f"name_{lang}", "—")
        lines.append(
            t(
                lang,
                "result_line",
                date=date,
                score=a.get("total_score") or 0,
                max=data["max_score"],
                percent=round(a.get("percent") or 0),
                level=escape(level),
            )
        )
    return "\n".join(lines)


def display_name(user) -> str:
    name = " ".join(filter(None, [user.first_name, user.last_name])).strip() or user.username or ""
    return escape(name)
