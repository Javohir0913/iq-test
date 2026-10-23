from iqbot.keyboards import main_menu, results_menu
from iqbot.texts import lang_of, results_text, t, texts

HTTPS = "https://iq.example.com"
HTTP = ""


def test_lang_detection():
    assert lang_of("ru") == "ru"
    assert lang_of("uk") == "ru"
    assert lang_of("uz") == "uz"
    assert lang_of("en") == "uz"
    assert lang_of(None) == "uz"


def test_i18n_keys_match():
    assert texts("uz").keys() == texts("ru").keys()
    assert texts("uz")["commands"].keys() == texts("ru")["commands"].keys()


def test_main_menu_webapp_only_with_https():
    kb = main_menu(HTTPS, "uz")
    assert kb.inline_keyboard[0][0].web_app.url == "https://iq.example.com/start?lang=uz"
    kb = main_menu(HTTP, "uz")
    assert all(b.web_app is None for row in kb.inline_keyboard for b in row)


def test_results_text_and_buttons():
    data = {
        "max_score": 245,
        "attempts": [
            {"attempt_id": "a1", "token": "tok1", "status": "finished", "started_at": "2026-10-23T10:00:00Z",
             "finished_at": "2026-10-23T10:30:00Z", "total_score": 182, "percent": 55.0,
             "level": {"name_uz": "Yuqori", "name_ru": "Высокий"}},
            {"attempt_id": "a2", "token": "tok2", "status": "in_progress", "started_at": "2026-10-23T11:00:00Z",
             "finished_at": None, "total_score": None, "percent": None, "level": None},
        ],
    }
    text = results_text("ru", data)
    assert "182/245" in text and "55%" in text and "Высокий" in text and "23.10.2026" in text
    kb = results_menu(HTTPS, "uz", data["attempts"])
    urls = [row[0].web_app.url for row in kb.inline_keyboard]
    assert urls[0] == "https://iq.example.com/result/a1?t=tok1"
    assert urls[1] == "https://iq.example.com/test/a2?t=tok2"
    assert t("uz", "continue_test") in kb.inline_keyboard[1][0].text
