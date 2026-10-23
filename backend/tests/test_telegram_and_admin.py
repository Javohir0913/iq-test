import json
import time

import pytest
from django.contrib.auth import get_user_model

from quiz.models import Attempt
from quiz.telegram import sign_init_data

pytestmark = pytest.mark.django_db
BOT = "123456:TEST-TOKEN"


def init_data(user_id=777, auth_date=None, bot=BOT):
    return sign_init_data(
        {
            "auth_date": str(auth_date or int(time.time())),
            "query_id": "AAE",
            "user": json.dumps({"id": user_id, "first_name": "Ali", "last_name": "Valiyev"}),
        },
        bot,
    )


def test_telegram_auth_ok(client):
    resp = client.post("/api/v1/telegram/auth", {"init_data": init_data()}, format="json")
    assert resp.status_code == 200
    assert resp.json()["user"]["full_name"] == "Ali Valiyev"


def test_telegram_auth_bad_signature(client):
    resp = client.post("/api/v1/telegram/auth", {"init_data": init_data(bot="999:OTHER")}, format="json")
    assert resp.status_code == 403


def test_telegram_auth_expired(client):
    resp = client.post(
        "/api/v1/telegram/auth", {"init_data": init_data(auth_date=int(time.time()) - 200000)}, format="json"
    )
    assert resp.status_code == 403


def test_attempt_stores_telegram_id(client, imported):
    resp = client.post(
        "/api/v1/attempts", {"full_name": "Ali Valiyev", "telegram_init_data": init_data(4242)}, format="json"
    )
    assert resp.status_code == 201
    assert Attempt.objects.get(pk=resp.json()["attempt_id"]).participant.telegram_id == 4242


@pytest.fixture
def admin_client(client):
    user = get_user_model().objects.create_superuser("root", "r@example.com", "pass12345")
    client.force_login(user)
    return client


def test_admin_pages(admin_client, make_attempt, answer):
    from quiz.models import Question

    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "C")
    question_id = Question.objects.get(number=1).id
    admin_client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)

    for url in [
        "/admin/",
        "/admin/quiz/question/",
        f"/admin/quiz/question/{question_id}/change/",
        "/admin/quiz/attempt/",
        f"/admin/quiz/attempt/{attempt_id}/change/",
        "/admin/quiz/participant/",
        "/admin/quiz/scorelevel/",
        "/admin/quiz/attempt/stats/",
    ]:
        resp = admin_client.get(url)
        assert resp.status_code == 200, url
    assert admin_client.get("/admin/quiz/testsettings/").status_code == 302


def test_admin_exports(admin_client, make_attempt):
    make_attempt()
    csv_resp = admin_client.get("/admin/quiz/attempt/export-csv")
    assert csv_resp.status_code == 200
    assert "Ali Valiyev" in csv_resp.content.decode("utf-8-sig")
    xlsx = admin_client.get("/admin/quiz/attempt/export-xlsx")
    assert xlsx.status_code == 200
    assert xlsx.content[:2] == b"PK"


def test_admin_option_formset_rejects_two_sevens(admin_client, imported):
    from quiz.models import Question

    q = Question.objects.get(number=1)
    data = {
        "number": q.number, "order": q.order, "is_active": "on", "type": q.type, "category": q.category,
        "prompt_uz": q.prompt_uz, "prompt_ru": q.prompt_ru, "logic_uz": q.logic_uz, "logic_ru": "",
        "options-TOTAL_FORMS": "6", "options-INITIAL_FORMS": "6", "options-MIN_NUM_FORMS": "6",
        "options-MAX_NUM_FORMS": "6",
    }
    for i, o in enumerate(q.options.order_by("letter")):
        data.update({
            f"options-{i}-id": o.id, f"options-{i}-question": q.id, f"options-{i}-letter": o.letter,
            f"options-{i}-value": o.value, f"options-{i}-points": 7 if i < 2 else o.points,
            f"options-{i}-reason_uz": o.reason_uz,
        })
    resp = admin_client.post(f"/admin/quiz/question/{q.id}/change/", data)
    assert resp.status_code == 200  # forma xato bilan qaytdi
    assert "aniq bitta 7" in resp.content.decode()

    # 7 ni boshqa variantga ko‘chirish (F → A) muvaffaqiyatli saqlanadi
    points = {o.letter: o.points for o in q.options.all()}
    seven = next(k for k, v in points.items() if v == 7)
    new_seven = "A" if seven != "A" else "B"
    for i, o in enumerate(q.options.order_by("letter")):
        p = 7 if o.letter == new_seven else (5 if o.letter == seven else o.points)
        data[f"options-{i}-points"] = p
    resp = admin_client.post(f"/admin/quiz/question/{q.id}/change/", data)
    assert resp.status_code == 302, resp.content.decode()[:2000]
    assert q.options.get(points=7).letter == new_seven


# --- Bot integratsiyasi ---------------------------------------------------------


def _finish_tg_attempt(client, telegram_id=555, language="uz"):
    resp = client.post(
        "/api/v1/attempts",
        {"full_name": "Ali <Valiyev>", "language": language, "telegram_init_data": init_data(telegram_id)},
        format="json",
    )
    data = resp.json()
    headers = {"HTTP_X_ATTEMPT_TOKEN": data["token"]}
    client.put(f"/api/v1/attempts/{data['attempt_id']}/answers/1", {"letter": "C"}, format="json", **headers)
    client.post(f"/api/v1/attempts/{data['attempt_id']}/finish", **headers)
    return data


def test_bot_results_requires_secret(client, imported):
    assert client.get("/api/v1/bot/results?telegram_id=1").status_code == 403
    assert client.get("/api/v1/bot/results?telegram_id=1", HTTP_X_BOT_TOKEN="wrong").status_code == 403
    assert client.get("/api/v1/bot/results", HTTP_X_BOT_TOKEN=BOT).status_code == 400


def test_bot_results_lists_user_attempts(client, imported):
    data = _finish_tg_attempt(client, 555)
    _finish_tg_attempt(client, 999)
    resp = client.get("/api/v1/bot/results?telegram_id=555", HTTP_X_BOT_TOKEN=BOT)
    assert resp.status_code == 200
    body = resp.json()
    assert body["max_score"] == 245
    assert [a["attempt_id"] for a in body["attempts"]] == [data["attempt_id"]]
    assert body["attempts"][0]["total_score"] == 7
    assert body["attempts"][0]["token"] == data["token"]


def test_meta_exposes_bot_username(client, imported):
    assert client.get("/api/v1/test/meta").json()["telegram_bot"] == "mantiqiy_test_bot"


def test_finish_sends_telegram_message(client, imported, settings, monkeypatch, django_capture_on_commit_callbacks):
    import threading

    from quiz import telegram

    settings.TELEGRAM_NOTIFY_RESULTS = True
    settings.PUBLIC_URL = "https://iq.example.com"
    sent = []
    monkeypatch.setattr(telegram, "bot_api", lambda method, payload=None, timeout=8: sent.append((method, payload)))

    class SyncThread:
        def __init__(self, target, daemon=None):
            self.target = target

        def start(self):
            self.target()

    monkeypatch.setattr(threading, "Thread", SyncThread)
    with django_capture_on_commit_callbacks(execute=True):
        data = _finish_tg_attempt(client, 4242, language="ru")

    assert len(sent) == 1
    method, payload = sent[0]
    assert method == "sendMessage"
    assert payload["chat_id"] == 4242
    assert "7 / 245" in payload["text"]
    assert "&lt;Valiyev&gt;" in payload["text"]  # HTML xavfsiz
    assert "тест завершён" in payload["text"]
    url = payload["reply_markup"]["inline_keyboard"][0][0]["web_app"]["url"]
    assert url == f"https://iq.example.com/result/{data['attempt_id']}?t={data['token']}"


def test_no_message_without_telegram(client, make_attempt, answer, settings, monkeypatch):
    from quiz import telegram

    settings.TELEGRAM_NOTIFY_RESULTS = True
    sent = []
    monkeypatch.setattr(telegram, "bot_api", lambda *a, **k: sent.append(a))
    attempt_id, token = make_attempt()
    client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    assert sent == []
