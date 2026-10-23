import json
import time

import pytest

from quiz.auth import sign_widget_data
from quiz.models import Attempt, TelegramAccount
from quiz.telegram import sign_init_data

pytestmark = pytest.mark.django_db
BOT = "123456:TEST-TOKEN"


def widget(user_id=101, **extra):
    return sign_widget_data(
        {"id": user_id, "first_name": "Aziza", "last_name": "Karimova", "username": "aziza", "auth_date": int(time.time()), **extra},
        BOT,
    )


def login(client, user_id=101):
    resp = client.post("/api/v1/auth/telegram/widget", widget(user_id), format="json")
    assert resp.status_code == 200, resp.content
    return resp.json()["token"]


def test_widget_login_creates_account(client):
    resp = client.post("/api/v1/auth/telegram/widget", widget(), format="json")
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["full_name"] == "Aziza Karimova"
    assert TelegramAccount.objects.get(telegram_id=101).username == "aziza"
    me = client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {body['token']}")
    assert me.status_code == 200 and me.json()["user"]["telegram_id"] == 101


@pytest.mark.parametrize(
    "mutate",
    [
        lambda d: d.update(first_name="Boshqa"),  # imzodan keyin o‘zgartirilgan
        lambda d: d.update(hash="0" * 64),
        lambda d: d.pop("hash"),
    ],
)
def test_widget_login_rejects_tampered(client, mutate):
    data = widget()
    mutate(data)
    assert client.post("/api/v1/auth/telegram/widget", data, format="json").status_code == 403


def test_widget_login_rejects_old(client):
    data = sign_widget_data({"id": 5, "first_name": "A", "auth_date": int(time.time()) - 200000}, BOT)
    assert client.post("/api/v1/auth/telegram/widget", data, format="json").status_code == 403


def test_webapp_login(client):
    init = sign_init_data(
        {"auth_date": str(int(time.time())), "user": json.dumps({"id": 202, "first_name": "Oleg", "language_code": "ru"})}, BOT
    )
    resp = client.post("/api/v1/auth/telegram/webapp", {"init_data": init}, format="json")
    assert resp.status_code == 200
    assert TelegramAccount.objects.get(telegram_id=202).language_code == "ru"


def test_bad_bearer(client):
    assert client.get("/api/v1/auth/me", HTTP_AUTHORIZATION="Bearer nonsense").status_code == 401
    assert client.get("/api/v1/auth/me").status_code == 401


def test_auth_required_blocks_anonymous_attempt(client, imported, settings):
    settings.REQUIRE_TELEGRAM_AUTH = True
    assert client.get("/api/v1/test/meta").json()["auth_required"] is True
    resp = client.post("/api/v1/attempts", {"full_name": "Ali Valiyev"}, format="json")
    assert resp.status_code == 401
    token = login(client)
    resp = client.post("/api/v1/attempts", {"full_name": "Aziza Karimova"}, format="json", HTTP_AUTHORIZATION=f"Bearer {token}")
    assert resp.status_code == 201
    assert Attempt.objects.get(pk=resp.json()["attempt_id"]).participant.telegram_id == 101


def test_my_attempts_and_owner_access(client, imported, settings):
    settings.REQUIRE_TELEGRAM_AUTH = True
    token = login(client, 101)
    other = login(client, 999)
    created = client.post("/api/v1/attempts", {"full_name": "Aziza"}, format="json", HTTP_AUTHORIZATION=f"Bearer {token}").json()
    aid = created["attempt_id"]

    mine = client.get("/api/v1/me/attempts", HTTP_AUTHORIZATION=f"Bearer {token}").json()
    assert [a["attempt_id"] for a in mine["attempts"]] == [aid]
    assert client.get("/api/v1/me/attempts", HTTP_AUTHORIZATION=f"Bearer {other}").json()["attempts"] == []

    # Egasi attempt tokenisiz (boshqa qurilmadan) kira oladi, begona – yo‘q
    assert client.get(f"/api/v1/attempts/{aid}/questions", HTTP_AUTHORIZATION=f"Bearer {token}").status_code == 200
    assert client.get(f"/api/v1/attempts/{aid}/questions", HTTP_AUTHORIZATION=f"Bearer {other}").status_code == 403
    for body in mine["attempts"]:
        assert "points" not in json.dumps(body)


def _create(client, token, name):
    return client.post("/api/v1/attempts", {"full_name": name}, format="json", HTTP_AUTHORIZATION=f"Bearer {token}")


def test_name_locked_after_first_attempt(client, imported, settings):
    settings.REQUIRE_TELEGRAM_AUTH = True
    token = login(client, 303)
    me = client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}").json()["user"]
    assert me["name_locked"] is False and me["real_name"] == ""

    first = _create(client, token, "Aziza Karimova").json()
    assert TelegramAccount.objects.get(telegram_id=303).real_name == "Aziza Karimova"

    # Keyingi urinishda boshqa ism yuborilsa ham qulflangan ism ishlatiladi
    second = _create(client, token, "Boshqa Odam").json()
    names = {a.participant.full_name for a in Attempt.objects.filter(pk__in=[first["attempt_id"], second["attempt_id"]])}
    assert names == {"Aziza Karimova"}
    me = client.get("/api/v1/auth/me", HTTP_AUTHORIZATION=f"Bearer {token}").json()["user"]
    assert me["name_locked"] is True and me["real_name"] == "Aziza Karimova"


def test_admin_rename_updates_past_attempts(client, imported, settings):
    from django.contrib.auth import get_user_model

    settings.REQUIRE_TELEGRAM_AUTH = True
    token = login(client, 404)
    aid = _create(client, token, "Xato Ism").json()["attempt_id"]
    account = TelegramAccount.objects.get(telegram_id=404)

    admin = get_user_model().objects.create_superuser("root2", "r2@example.com", "pass12345")
    client.force_login(admin)
    resp = client.post(f"/admin/quiz/telegramaccount/{account.pk}/change/", {"real_name": "To‘g‘ri Ism"})
    assert resp.status_code == 302, resp.content.decode()[:500]
    assert Attempt.objects.get(pk=aid).participant.full_name == "To‘g‘ri Ism"
    assert client.get("/admin/quiz/attempt/").status_code == 200
    assert client.get("/admin/quiz/telegramaccount/").status_code == 200
