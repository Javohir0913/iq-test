from iqbot.keyboards import invite_menu, language_menu, main_menu, results_menu
from iqbot.texts import lang_of, results_text, stages_text, t, texts

HTTPS = "https://iq.example.com"
HTTP = ""

PROGRESS = {
    "subscription_required": False,
    "subscribed": True,
    "channels": [],
    "friends": 1,
    "pending_friends": 0,
    "referral_link": "https://t.me/mantiqiy_test_bot?start=ref42",
    "stages": [
        {"number": 1, "question_count": 10, "duration_minutes": 12, "friends_required": 0, "certificate": False,
         "unlocked": True, "missing_friends": 0},
        {"number": 2, "question_count": 15, "duration_minutes": 18, "friends_required": 1, "certificate": False,
         "unlocked": True, "missing_friends": 0},
        {"number": 3, "question_count": 20, "duration_minutes": 25, "friends_required": 2, "certificate": True,
         "unlocked": False, "missing_friends": 1},
    ],
}


def buttons(kb):
    return [b for row in kb.inline_keyboard for b in row]


def test_lang_detection():
    assert lang_of("ru") == "ru"
    assert lang_of("uk") == "ru"
    assert lang_of("uz") == "uz"
    assert lang_of("en") == "uz"
    assert lang_of(None) == "uz"
    assert lang_of("ru", "en") == "en"
    assert lang_of("ru", "xx") == "ru"


def test_i18n_keys_match():
    for lang in ("ru", "en"):
        assert texts("uz").keys() == texts(lang).keys()
        assert texts("uz")["commands"].keys() == texts(lang)["commands"].keys()


def test_main_menu_stage_buttons():
    kb = main_menu(HTTPS, "uz", PROGRESS)
    urls = [b.web_app.url for b in buttons(kb) if b.web_app]
    assert urls == [
        "https://iq.example.com/start?lang=uz&stage=1",
        "https://iq.example.com/start?lang=uz&stage=2",
    ]
    locked = [b for b in buttons(kb) if b.callback_data == "invite"]
    assert len(locked) == 2  # yopiq bosqich + "do‘stlarni taklif qilish"
    assert any(b.callback_data == "lang" for b in buttons(kb))


def test_main_menu_channels_first():
    progress = {
        **PROGRESS,
        "subscription_required": True,
        "subscribed": False,
        "channels": [
            {"title": "Kanal A", "url": "https://t.me/kanal_a", "subscribed": False},
            {"title": "Kanal B", "url": "https://t.me/kanal_b", "subscribed": True},
        ],
    }
    kb = main_menu(HTTPS, "ru", progress)
    assert [b.url for b in buttons(kb) if b.url] == ["https://t.me/kanal_a"]
    assert not any(b.web_app for b in buttons(kb))
    assert any(b.callback_data == "check" for b in buttons(kb))


def test_main_menu_without_https():
    kb = main_menu(HTTP, "uz", PROGRESS)
    assert all(b.web_app is None for b in buttons(kb))


def test_stages_text_and_invite():
    text = stages_text("en", PROGRESS)
    assert "Stage 3" in text and "certificate" in text and "🔒" in text
    kb = invite_menu("uz", PROGRESS["referral_link"])
    assert "ref42" in buttons(kb)[0].url
    assert [b.callback_data for b in buttons(language_menu())] == ["setlang:uz", "setlang:ru", "setlang:en"]


def test_results_text_and_buttons():
    data = {
        "attempts": [
            {"attempt_id": "a1", "token": "tok1", "status": "finished", "started_at": "2026-10-23T10:00:00Z",
             "finished_at": "2026-10-23T10:30:00Z", "total_score": 105, "max_score": 140, "percent": 56.3,
             "stage": {"number": 3, "certificate": True},
             "level": {"name_uz": "Yuqori", "name_ru": "Высокий", "name_en": "High"}},
            {"attempt_id": "a2", "token": "tok2", "status": "in_progress", "started_at": "2026-10-23T11:00:00Z",
             "finished_at": None, "total_score": None, "max_score": 70, "percent": None, "level": None,
             "stage": {"number": 1, "certificate": False}},
        ],
    }
    text = results_text("ru", data)
    assert "105/140" in text and "56%" in text and "Высокий" in text and "23.10.2026" in text and "этап 3" in text
    assert "High" in results_text("en", data)
    kb = results_menu(HTTPS, "uz", data["attempts"])
    urls = [row[0].web_app.url for row in kb.inline_keyboard]
    assert urls[0] == "https://iq.example.com/result/a1?t=tok1"
    assert urls[1] == "https://iq.example.com/test/a2?t=tok2"
    assert t("uz", "continue_test") in kb.inline_keyboard[1][0].text
