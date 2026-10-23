import json

import pytest
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from quiz.models import Option, Question

pytestmark = pytest.mark.django_db


def test_import_creates_35_questions_with_matching_points(imported, questions_data):
    assert Question.objects.count() == 35
    assert Option.objects.count() == 35 * 6
    for q in questions_data["questions"]:
        db_q = Question.objects.get(number=q["number"])
        assert db_q.type == q["type"]
        assert db_q.category == q["category"]
        assert db_q.prompt_uz == q["prompt"]["uz"]
        assert db_q.prompt_ru == q["prompt"]["ru"]
        assert db_q.figure.storage.exists(db_q.figure.name)
        db_points = {o.letter: o.points for o in db_q.options.all()}
        assert db_points == {o["letter"]: o["points"] for o in q["options"]}
        seven = [o.letter for o in db_q.options.all() if o.points == 7]
        assert seven == [q["correct"]]
        for o in db_q.options.all():
            if q["type"] == "image":
                assert o.image and o.image.storage.exists(o.image.name)
            else:
                assert o.value is not None


def test_import_is_idempotent(imported, questions_data):
    from tests.conftest import QUESTIONS_JSON

    names_before = sorted(Question.objects.values_list("figure", flat=True))
    call_command("import_questions", str(QUESTIONS_JSON), verbosity=0)
    assert Question.objects.count() == 35
    assert Option.objects.count() == 210
    assert sorted(Question.objects.values_list("figure", flat=True)) == names_before


def test_import_if_empty_skips(imported):
    from tests.conftest import QUESTIONS_JSON

    Question.objects.filter(number=1).update(prompt_uz="O‘zgartirilgan")
    call_command("import_questions", str(QUESTIONS_JSON), "--if-empty", verbosity=0)
    assert Question.objects.get(number=1).prompt_uz == "O‘zgartirilgan"


def _write_variant(tmp_path, questions_data, mutate):
    import shutil

    from tests.conftest import QUESTIONS_JSON

    data = json.loads(json.dumps(questions_data))
    data["questions"] = data["questions"][:1]
    mutate(data["questions"][0])
    shutil.copytree(QUESTIONS_JSON.parent / "assets" / "q01", tmp_path / "assets" / "q01")
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "mutate",
    [
        lambda q: q["options"].__setitem__(0, {**q["options"][0], "points": 7}),  # ikkita 7
        lambda q: [o.update(points=6) for o in q["options"] if o["points"] == 7],  # 7 yo‘q
        lambda q: q["options"].__setitem__(1, {**q["options"][1], "points": 2}),  # 3 dan kam
        lambda q: q["options"].pop(),  # 5 ta variant
        lambda q: q.update(correct="A"),  # to‘g‘ri javob 7 bilan mos emas
    ],
)
def test_import_rejects_invalid(db, tmp_path, questions_data, mutate):
    path = _write_variant(tmp_path, questions_data, mutate)
    with pytest.raises(CommandError):
        call_command("import_questions", str(path), verbosity=0)
    assert Question.objects.count() == 0


def test_db_constraints(imported):
    q = Question.objects.get(number=1)
    with pytest.raises(IntegrityError), transaction.atomic():
        Option.objects.filter(question=q, letter="A").update(points=8)
    with pytest.raises(IntegrityError), transaction.atomic():
        Option.objects.filter(question=q, letter="A").update(points=7)  # ikkinchi 7
    with pytest.raises(IntegrityError), transaction.atomic():
        Option.objects.create(question=q, letter="A", points=5)


def test_model_clean_requires_single_seven(imported):
    q = Question.objects.get(number=1)
    q.full_clean()
    Option.objects.filter(question=q, points=7).update(points=6)
    with pytest.raises(ValidationError):
        q.full_clean()
