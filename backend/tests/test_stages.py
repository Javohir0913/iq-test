"""Bosqichlar, majburiy kanallar, referal (do‘st taklif qilish) va bot tili."""

import pytest

from quiz import progress
from quiz.auth import issue_token
from quiz.models import Attempt, Question, RequiredChannel, Stage, TelegramAccount, TestSettings, normalize_chat
from quiz.services import pick_questions

pytestmark = pytest.mark.django_db

BOT = "123456:TEST-TOKEN"

# Migratsiyadagi standart bosqichlar: (savollar, maks. qiyinlik, do‘stlar, sertifikat)
DEFAULTS = {1: (10, 1, 0, False), 2: (15, 2, 1, False), 3: (20, 3, 2, True)}


@pytest.fixture
def real_stages(imported):
    """conftest soddalashtirgan bosqichlarni haqiqiy (standart) holatiga qaytaradi."""
    for number, (count, difficulty, friends, certificate) in DEFAULTS.items():
        Stage.objects.filter(number=number).update(
            question_count=count, max_difficulty=difficulty, friends_required=friends, certificate=certificate
        )


def account(telegram_id, **extra):
    return TelegramAccount.objects.create(telegram_id=telegram_id, first_name=f"U{telegram_id}", **extra)


def bearer(acc):
    return {"HTTP_AUTHORIZATION": f"Bearer {issue_token(acc)}"}


def start(client, stage, acc=None):
    headers = bearer(acc) if acc else {}
    return client.post("/api/v1/attempts", {"full_name": "Ali Valiyev", "stage": stage}, format="json", **headers)


def test_default_stages_created_by_migration(db):
    stages = {s.number: s for s in Stage.objects.all()}
    assert set(stages) == {1, 2, 3}
    for number, (count, difficulty, friends, certificate) in DEFAULTS.items():
        s = stages[number]
        assert (s.question_count, s.max_difficulty, s.friends_required, s.certificate) == (
            count,
            difficulty,
            friends,
            certificate,
        )


def test_pick_questions_respects_difficulty_and_is_random(real_stages):
    stage1 = Stage.objects.get(number=1)
    easy = set(Question.objects.filter(difficulty=1).values_list("id", flat=True))
    picks = [pick_questions(stage1) for _ in range(5)]
    for ids in picks:
        assert len(ids) == 10 and len(set(ids)) == 10
        assert set(ids) <= easy
    assert len({tuple(ids) for ids in picks}) > 1  # har safar boshqacha


def test_pick_questions_fills_from_harder_when_pool_is_small(real_stages):
    stage1 = Stage.objects.get(number=1)
    Question.objects.filter(difficulty=1).exclude(number__in=[1, 2, 3]).update(difficulty=2)
    ids = pick_questions(stage1)
    assert len(ids) == 10
    assert set(Question.objects.filter(number__in=[1, 2, 3]).values_list("id", flat=True)) <= set(ids)


def test_stage_attempt_uses_only_its_questions(client, real_stages, answer):
    resp = start(client, 1)
    assert resp.status_code == 201, resp.content
    data = resp.json()
    attempt = Attempt.objects.get(pk=data["attempt_id"])
    assert attempt.stage.number == 1 and len(attempt.question_ids) == 10
    questions = client.get(
        f"/api/v1/attempts/{data['attempt_id']}/questions", HTTP_X_ATTEMPT_TOKEN=data["token"]
    ).json()
    assert [q["number"] for q in questions["questions"]] == [
        Question.objects.get(pk=qid).number for qid in attempt.question_ids
    ]
    assert questions["stage"] == {"number": 1, "certificate": False}
    outside = Question.objects.exclude(id__in=attempt.question_ids).first()
    assert answer(data["attempt_id"], data["token"], outside.number, "A").status_code == 404


def test_no_certificate_on_stage_one(client, real_stages):
    data = start(client, 1).json()
    headers = {"HTTP_X_ATTEMPT_TOKEN": data["token"]}
    result = client.post(f"/api/v1/attempts/{data['attempt_id']}/finish", **headers).json()
    assert result["certificate_available"] is False
    assert result["verify_code"] == ""
    assert result["max_score"] == 70
    pdf = client.get(f"/api/v1/attempts/{data['attempt_id']}/certificate.pdf?token={data['token']}")
    assert pdf.status_code == 403
    code = Attempt.objects.get(pk=data["attempt_id"]).verify_code
    assert client.get(f"/api/v1/verify/{code}").status_code == 404


def test_friends_required_for_stage_two_and_three(client, real_stages):
    assert start(client, 2).json()["error"] == "friends_required"
    me = account(100)
    assert start(client, 2, me).status_code == 403
    friend = account(101, referred_by=me)
    progress.confirm_referral(friend)
    assert start(client, 2, me).status_code == 201
    assert start(client, 3, me).json()["error"] == "friends_required"
    friend2 = account(102, referred_by=me)
    progress.confirm_referral(friend2)
    resp = start(client, 3, me)
    assert resp.status_code == 201
    assert Attempt.objects.get(pk=resp.json()["attempt_id"]).has_certificate


def test_unknown_stage(client, real_stages):
    assert start(client, 9).json()["error"] == "stage_not_found"
    Stage.objects.filter(number=1).update(is_active=False)
    assert start(client, 1).json()["error"] == "stage_not_found"


def test_subscription_required(client, real_stages, monkeypatch):
    member = {"value": False}
    monkeypatch.setattr(progress, "is_member", lambda chat, telegram_id: member["value"])
    RequiredChannel.objects.create(chat="https://t.me/mening_kanalim", title="Kanal")
    me = account(200)

    # Obuna o‘chiq – kanal bo‘lsa ham tekshirilmaydi
    assert start(client, 1, me).status_code == 201
    settings_obj = TestSettings.load()
    settings_obj.subscription_required = True
    settings_obj.save()

    resp = start(client, 1, me)
    assert resp.status_code == 403 and resp.json()["error"] == "subscription_required"
    assert start(client, 1).json()["error"] == "subscription_required"  # Telegram’siz kirib bo‘lmaydi
    body = client.get("/api/v1/me/progress", **bearer(me)).json()
    assert body["subscription_required"] is True and body["subscribed"] is False
    assert body["channels"] == [{"title": "Kanal", "url": "https://t.me/mening_kanalim", "subscribed": False}]
    assert not any(s["unlocked"] for s in body["stages"])

    member["value"] = True
    assert start(client, 1, me).status_code == 201


def test_unverifiable_channel_does_not_block(client, real_stages, monkeypatch):
    """Bot kanalda admin bo‘lmasa (tekshirib bo‘lmaydi) – foydalanuvchi to‘sib qo‘yilmaydi."""
    monkeypatch.setattr(progress, "is_member", lambda chat, telegram_id: None)
    RequiredChannel.objects.create(chat="@kanal", title="Kanal")
    s = TestSettings.load()
    s.subscription_required = True
    s.save()
    assert start(client, 1, account(300)).status_code == 201


def test_normalize_chat():
    assert normalize_chat("https://t.me/kanal?x=1") == "@kanal"
    assert normalize_chat("@kanal") == "@kanal"
    assert normalize_chat("kanal") == "@kanal"
    assert normalize_chat("-1001234567890") == "-1001234567890"


def register(client, telegram_id, start_param=""):
    return client.post(
        "/api/v1/bot/register",
        {"id": telegram_id, "first_name": f"U{telegram_id}", "language_code": "ru", "start_param": start_param},
        format="json",
        HTTP_X_BOT_TOKEN=BOT,
    )


def test_bot_register_and_referral(client, real_stages):
    assert client.post("/api/v1/bot/register", {"id": 1}, format="json").status_code == 403
    me = register(client, 500).json()
    assert me["language"] == "ru"
    assert me["referral_link"] == "https://t.me/mantiqiy_test_bot?start=ref500"
    assert [s["unlocked"] for s in me["stages"]] == [True, False, False]

    register(client, 501, "ref500")  # yangi do‘st – hisoblanadi
    register(client, 500, "ref501")  # eski foydalanuvchi – referal yozilmaydi
    register(client, 502, "ref502")  # o‘zini taklif qila olmaydi
    register(client, 503, "refABC")  # noto‘g‘ri
    assert TelegramAccount.objects.get(telegram_id=501).referred_by.telegram_id == 500
    assert TelegramAccount.objects.get(telegram_id=500).referred_by is None
    assert TelegramAccount.objects.get(telegram_id=502).referred_by is None
    assert TelegramAccount.objects.get(telegram_id=503).referred_by is None

    body = client.get("/api/v1/bot/progress?telegram_id=500", HTTP_X_BOT_TOKEN=BOT).json()
    assert body["friends"] == 1
    assert [s["unlocked"] for s in body["stages"]] == [True, True, False]


def test_referral_counts_only_after_subscription(client, real_stages, monkeypatch):
    subscribed = set()
    monkeypatch.setattr(progress, "is_member", lambda chat, telegram_id: telegram_id in subscribed)
    RequiredChannel.objects.create(chat="@kanal", title="Kanal")
    s = TestSettings.load()
    s.subscription_required = True
    s.save()

    register(client, 600)
    register(client, 601, "ref600")
    assert client.get("/api/v1/bot/progress?telegram_id=600", HTTP_X_BOT_TOKEN=BOT).json()["pending_friends"] == 1
    assert progress.confirmed_friends(TelegramAccount.objects.get(telegram_id=600)) == 0

    subscribed.add(601)
    register(client, 601)  # do‘st botga qaytib "Tekshirish" bosadi
    assert progress.confirmed_friends(TelegramAccount.objects.get(telegram_id=600)) == 1


def test_bot_language(client, real_stages):
    register(client, 700)
    resp = client.post(
        "/api/v1/bot/language", {"telegram_id": 700, "language": "en"}, format="json", HTTP_X_BOT_TOKEN=BOT
    )
    assert resp.status_code == 200
    assert register(client, 700).json()["language"] == "en"
    assert (
        client.post(
            "/api/v1/bot/language", {"telegram_id": 700, "language": "de"}, format="json", HTTP_X_BOT_TOKEN=BOT
        ).status_code
        == 400
    )


def test_english_attempt_and_certificate(client, imported):
    data = client.post("/api/v1/attempts", {"full_name": "John Smith", "language": "en"}, format="json").json()
    headers = {"HTTP_X_ATTEMPT_TOKEN": data["token"]}
    questions = client.get(f"/api/v1/attempts/{data['attempt_id']}/questions", **headers).json()["questions"]
    assert all(q["prompt"]["en"] for q in questions)
    result = client.post(f"/api/v1/attempts/{data['attempt_id']}/finish", **headers).json()
    assert result["level"]["name_en"] == "Beginner"
    assert {c["key"]: c["name_en"] for c in result["categories"]}["spatial"] == "Spatial thinking"
    pdf = client.get(f"/api/v1/attempts/{data['attempt_id']}/certificate.pdf?token={data['token']}&lang=en")
    assert pdf.status_code == 200 and pdf.content.startswith(b"%PDF")


def test_admin_pages_for_new_models(client, imported, django_user_model, monkeypatch):
    from quiz import telegram

    def offline(*args, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr(telegram, "bot_api", offline)
    admin = django_user_model.objects.create_superuser("root", "root@example.com", "pw")
    client.force_login(admin)
    RequiredChannel.objects.create(chat="@kanal", title="Kanal")
    for url in ("/admin/quiz/stage/", "/admin/quiz/requiredchannel/", "/admin/quiz/scorelevel/", "/admin/quiz/attempt/stats/"):
        assert client.get(url).status_code == 200, url
