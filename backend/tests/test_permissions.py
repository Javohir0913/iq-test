import uuid
from datetime import timedelta

import pytest
from django.utils import timezone

from quiz.models import Attempt

pytestmark = pytest.mark.django_db


def test_requires_token(client, make_attempt):
    attempt_id, _ = make_attempt()
    assert client.get(f"/api/v1/attempts/{attempt_id}/questions").status_code == 403


def test_other_token_rejected(client, make_attempt, answer):
    a_id, _ = make_attempt("Ali Valiyev")
    _, b_token = make_attempt("Vali Aliyev")
    assert client.get(f"/api/v1/attempts/{a_id}/questions", HTTP_X_ATTEMPT_TOKEN=b_token).status_code == 403
    assert answer(a_id, b_token, 1, "A").status_code == 403
    assert client.post(f"/api/v1/attempts/{a_id}/finish", HTTP_X_ATTEMPT_TOKEN=b_token).status_code == 403
    assert client.get(f"/api/v1/attempts/{a_id}/result", HTTP_X_ATTEMPT_TOKEN=b_token).status_code == 403
    assert client.get(f"/api/v1/attempts/{a_id}/certificate.pdf?token={b_token}").status_code == 403


def test_unknown_attempt_404(client, imported):
    resp = client.get(f"/api/v1/attempts/{uuid.uuid4()}/questions", HTTP_X_ATTEMPT_TOKEN="x")
    assert resp.status_code == 404


def test_token_via_query_param(client, make_attempt):
    attempt_id, token = make_attempt()
    assert client.get(f"/api/v1/attempts/{attempt_id}/questions?token={token}").status_code == 200


def test_cannot_answer_after_finish(client, make_attempt, answer):
    attempt_id, token = make_attempt()
    client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    resp = answer(attempt_id, token, 1, "A")
    assert resp.status_code == 409
    assert resp.json()["error"] == "attempt_closed"


def test_result_before_finish_is_conflict(client, make_attempt):
    attempt_id, token = make_attempt()
    resp = client.get(f"/api/v1/attempts/{attempt_id}/result", HTTP_X_ATTEMPT_TOKEN=token)
    assert resp.status_code == 409


def test_expired_attempt_rejects_answers_and_autofinishes(client, make_attempt, answer, get_attempt):
    attempt_id, token = make_attempt()
    answer(attempt_id, token, 1, "C")
    Attempt.objects.filter(pk=attempt_id).update(expires_at=timezone.now() - timedelta(minutes=1))

    resp = answer(attempt_id, token, 2, "D")
    assert resp.status_code == 409
    assert resp.json()["error"] in {"attempt_expired", "attempt_closed"}

    resp = client.get(f"/api/v1/attempts/{attempt_id}/result", HTTP_X_ATTEMPT_TOKEN=token)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "expired"
    assert data["total_score"] == 7  # faqat muddat ichida berilgan javob hisoblanadi
    attempt = get_attempt(attempt_id)
    assert attempt.finished_at <= attempt.expires_at


def test_questions_endpoint_expires_attempt(client, make_attempt):
    attempt_id, token = make_attempt()
    Attempt.objects.filter(pk=attempt_id).update(expires_at=timezone.now() - timedelta(seconds=5))
    data = client.get(f"/api/v1/attempts/{attempt_id}/questions", HTTP_X_ATTEMPT_TOKEN=token).json()
    assert data["status"] == "expired"


def test_expiry_uses_test_duration(client, make_attempt, get_attempt):
    from quiz.models import Stage, TestSettings

    # Vaqt endi bosqichdan olinadi (TestSettings.duration_minutes – faqat eski urinishlar uchun)
    s = TestSettings.load()
    s.duration_minutes = 40
    s.save()
    Stage.objects.filter(number=3).update(duration_minutes=15)
    attempt_id, _ = make_attempt()
    a = get_attempt(attempt_id)
    assert abs((a.expires_at - a.started_at).total_seconds() - 15 * 60) < 5


@pytest.mark.parametrize(
    "payload,field",
    [
        ({"full_name": ""}, "full_name"),
        ({"full_name": "A"}, "full_name"),
        ({"full_name": "Ali Valiyev", "phone": "12345"}, "phone"),
        ({"full_name": "Ali Valiyev", "language": "de"}, "language"),
    ],
)
def test_create_validation(client, imported, payload, field):
    resp = client.post("/api/v1/attempts", payload, format="json")
    assert resp.status_code == 400
    assert field in resp.json()


def test_phone_normalized(client, imported):
    resp = client.post(
        "/api/v1/attempts", {"full_name": "Ali Valiyev", "phone": "+998 (90) 123-45-67"}, format="json"
    )
    assert resp.status_code == 201
    assert Attempt.objects.get(pk=resp.json()["attempt_id"]).participant.phone == "+998901234567"


def test_invalid_letter(make_attempt, answer):
    attempt_id, token = make_attempt()
    assert answer(attempt_id, token, 1, "G").status_code == 400
    assert answer(attempt_id, token, 99, "A").status_code == 404


def test_certificate_pdf(client, make_attempt, answer):
    attempt_id, token = make_attempt("Олег Петров", language="ru")
    answer(attempt_id, token, 1, "C")
    assert client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf?token={token}").status_code == 409
    client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token)
    for lang in ("uz", "ru", "en"):
        resp = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf?token={token}&lang={lang}")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "application/pdf"
        assert resp.content.startswith(b"%PDF")


def test_throttling_configured(settings):
    from django.conf import settings as dj

    rates = dj.REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]
    assert {"anon", "attempt_create", "answer", "telegram"} <= set(rates)


def test_openapi_docs(client, imported):
    assert client.get("/api/schema").status_code == 200
    assert client.get("/api/docs").status_code == 200
