import json
from pathlib import Path

import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from quiz.models import Attempt

QUESTIONS_JSON = Path(__file__).resolve().parents[2] / "namunalar" / "questions.json"
if not QUESTIONS_JSON.exists():
    QUESTIONS_JSON = Path("/app/namunalar/questions.json")


@pytest.fixture(autouse=True)
def _test_settings(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"
    settings.REST_FRAMEWORK = {
        **settings.REST_FRAMEWORK,
        "DEFAULT_THROTTLE_CLASSES": [],
    }
    settings.TELEGRAM_BOT_TOKEN = "123456:TEST-TOKEN"
    settings.TELEGRAM_BOT_USERNAME = "mantiqiy_test_bot"
    settings.TELEGRAM_NOTIFY_RESULTS = False
    settings.REQUIRE_TELEGRAM_AUTH = False


@pytest.fixture
def questions_data():
    return json.loads(QUESTIONS_JSON.read_text(encoding="utf-8"))


@pytest.fixture
def imported(db):
    call_command("import_questions", str(QUESTIONS_JSON), verbosity=0)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def make_attempt(client, imported):
    def _make(full_name="Ali Valiyev", phone="", language="uz"):
        resp = client.post(
            "/api/v1/attempts", {"full_name": full_name, "phone": phone, "language": language}, format="json"
        )
        assert resp.status_code == 201, resp.content
        data = resp.json()
        return data["attempt_id"], data["token"]

    return _make


@pytest.fixture
def answer(client):
    def _answer(attempt_id, token, number, letter):
        return client.put(
            f"/api/v1/attempts/{attempt_id}/answers/{number}",
            {"letter": letter},
            format="json",
            HTTP_X_ATTEMPT_TOKEN=token,
        )

    return _answer


@pytest.fixture
def get_attempt():
    return lambda attempt_id: Attempt.objects.get(pk=attempt_id)
