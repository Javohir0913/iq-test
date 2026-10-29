import pytest

from quiz.models import Attempt, Participant, format_verify_code

pytestmark = pytest.mark.django_db


def finished(client, make_attempt, answer, name="Ali Valiyev"):
    attempt_id, token = make_attempt(name)
    answer(attempt_id, token, 1, "C")
    data = client.post(f"/api/v1/attempts/{attempt_id}/finish", HTTP_X_ATTEMPT_TOKEN=token).json()
    return attempt_id, token, data


def test_result_contains_verify_code(client, make_attempt, answer):
    attempt_id, _, data = finished(client, make_attempt, answer)
    code = Attempt.objects.get(pk=attempt_id).verify_code
    assert len(code) == 10
    assert data["verify_code"] == format_verify_code(code)


def test_verify_shows_server_data(client, make_attempt, answer):
    attempt_id, _, data = finished(client, make_attempt, answer)
    code = data["verify_code"]
    for variant in (code, code.replace("-", ""), code.lower()):
        resp = client.get(f"/api/v1/verify/{variant}")
        assert resp.status_code == 200, variant
        body = resp.json()
        assert body["valid"] is True
        assert body["full_name"] == "Ali Valiyev"
        assert body["total_score"] == 7 and body["max_score"] == Attempt.objects.get(pk=attempt_id).question_ids.__len__() * 7
    # Hech qanday maxfiy narsa yo‘q
    assert set(body) == {
        "valid", "code", "full_name", "finished_at", "total_score", "max_score", "percent", "stage", "level",
        "telegram_verified",
    }


def test_verify_reflects_admin_name_fix(client, make_attempt, answer):
    attempt_id, _, data = finished(client, make_attempt, answer, "Xato Ism")
    Participant.objects.filter(attempts__id=attempt_id).update(full_name="To‘g‘ri Ism")
    assert client.get(f"/api/v1/verify/{data['verify_code']}").json()["full_name"] == "To‘g‘ri Ism"


def test_verify_unknown_or_in_progress(client, make_attempt):
    assert client.get("/api/v1/verify/AAAA-BBBB-CC").status_code == 404
    attempt_id, _ = make_attempt()
    code = Attempt.objects.get(pk=attempt_id).verify_code
    assert client.get(f"/api/v1/verify/{code}").status_code == 404  # hali yakunlanmagan


def test_verify_code_does_not_open_attempt(client, make_attempt, answer):
    attempt_id, _, data = finished(client, make_attempt, answer)
    code = data["verify_code"].replace("-", "")
    assert client.get(f"/api/v1/attempts/{attempt_id}/result", HTTP_X_ATTEMPT_TOKEN=code).status_code == 403


def test_certificate_has_qr(client, make_attempt, answer, settings):
    settings.PUBLIC_URL = "https://iq.example.com"
    attempt_id, token, _ = finished(client, make_attempt, answer)
    pdf = client.get(f"/api/v1/attempts/{attempt_id}/certificate.pdf?token={token}").content
    assert pdf.startswith(b"%PDF") and len(pdf) > 10_000
