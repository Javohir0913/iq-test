import hmac
import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.exceptions import NotFound, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from .. import progress, services
from ..auth import account_from_init_data, account_from_request, account_payload, issue_token, upsert_account, validate_widget_data
from ..certificate import render_certificate
from ..models import (
    LANG_CODES,
    Answer,
    Attempt,
    Option,
    Participant,
    Question,
    TelegramAccount,
    format_verify_code,
    normalize_verify_code,
)
from ..telegram import TelegramAuthError, bot_username, validate_init_data
from .serializers import (
    AnswerSerializer,
    AttemptCreateSerializer,
    BotLanguageSerializer,
    BotRegisterSerializer,
    QuestionPublicSerializer,
    TelegramAuthSerializer,
)

logger = logging.getLogger(__name__)

TOKEN_PARAM = OpenApiParameter("X-Attempt-Token", str, OpenApiParameter.HEADER, required=True)


def error(code, http_status, **extra):
    return Response({"error": code, **extra}, status=http_status)


class AttemptAccessMixin:
    """Urinishni `token` orqali himoyalaydi (X-Attempt-Token sarlavhasi yoki ?token=)."""

    def get_attempt(self, request, attempt_id, for_update=False):
        qs = Attempt.objects.select_related("participant", "level")
        if for_update:
            qs = qs.select_for_update(of=("self",))
        try:
            attempt = qs.get(pk=attempt_id)
        except Attempt.DoesNotExist as exc:
            raise NotFound("attempt_not_found") from exc
        token = request.headers.get("X-Attempt-Token") or request.query_params.get("token") or ""
        if hmac.compare_digest(token.encode(), attempt.token.encode()):
            return attempt
        # Telegram orqali kirgan egasi tokensiz ham kira oladi (boshqa qurilmadan)
        account = account_from_request(request)
        if account and attempt.participant.telegram_id == account.telegram_id:
            return attempt
        raise PermissionDenied("invalid_token")


class TestMetaView(APIView):
    @extend_schema(
        summary="Test haqida umumiy ma’lumot",
        responses=inline_serializer(
            "TestMeta",
            {
                "question_count": serializers.IntegerField(),
                "duration_minutes": serializers.IntegerField(),
                "options_per_question": serializers.IntegerField(),
                "max_score": serializers.IntegerField(),
                "languages": serializers.ListField(child=serializers.CharField()),
                "telegram_bot": serializers.CharField(),
                "auth_required": serializers.BooleanField(),
            },
        ),
    )
    def get(self, request):
        stages = list(services.active_stages())
        bank = services.active_questions().count()
        top = stages[-1] if stages else None
        count = min(top.question_count, bank) if top else bank
        return Response(
            {
                "question_count": count,
                "duration_minutes": top.duration_minutes if top else 0,
                "options_per_question": 6,
                "max_score": services.score_bounds(count)[1],
                "bank_size": bank,
                "stages": [
                    {
                        "number": s.number,
                        "question_count": min(s.question_count, bank),
                        "duration_minutes": s.duration_minutes,
                        "friends_required": s.friends_required,
                        "certificate": s.certificate,
                    }
                    for s in stages
                ],
                "languages": LANG_CODES,
                "telegram_bot": bot_username(),
                "auth_required": settings.REQUIRE_TELEGRAM_AUTH,
            }
        )


class AttemptCreateView(APIView):
    throttle_scope = "attempt_create"

    @extend_schema(summary="Urinish yaratish", request=AttemptCreateSerializer)
    def post(self, request):
        serializer = AttemptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not services.active_questions().exists():
            return error("no_questions", status.HTTP_503_SERVICE_UNAVAILABLE)
        stage = services.active_stages().filter(number=data["stage"]).first()
        if stage is None:
            return error("stage_not_found", status.HTTP_400_BAD_REQUEST)

        telegram_id = None
        account = account_from_request(request)
        if account is None and data.get("telegram_init_data"):
            try:
                account = account_from_init_data(data["telegram_init_data"])
            except TelegramAuthError as exc:
                logger.info("Telegram initData rad etildi: %s", exc)
        if account is not None:
            telegram_id = account.telegram_id
        elif settings.REQUIRE_TELEGRAM_AUTH:
            return error("auth_required", status.HTTP_401_UNAUTHORIZED)

        denied = progress.stage_access_error(account, stage)
        if denied:
            return error(denied, status.HTTP_403_FORBIDDEN, stage=stage.number)

        full_name = data["full_name"]
        with transaction.atomic():
            if account is not None:
                # Ism akkauntga qulflanadi: birinchi marta saqlanadi, keyin o‘sha ism ishlatiladi
                account = type(account).objects.select_for_update().get(pk=account.pk)
                if account.real_name:
                    full_name = account.real_name
                else:
                    account.real_name = full_name
                    account.save(update_fields=["real_name"])
            participant = Participant.objects.create(
                full_name=full_name,
                phone=data["phone"],
                language=data["language"],
                telegram_id=telegram_id,
            )
            attempt = services.create_attempt(participant, stage)

        return Response(
            {
                "attempt_id": str(attempt.id),
                "token": attempt.token,
                "expires_at": attempt.expires_at,
                "server_time": timezone.now(),
            },
            status=status.HTTP_201_CREATED,
        )


class AttemptQuestionsView(AttemptAccessMixin, APIView):
    @extend_schema(summary="Savollar (ballarsiz) va tanlangan javoblar", parameters=[TOKEN_PARAM])
    def get(self, request, attempt_id):
        attempt = services.expire_if_needed(self.get_attempt(request, attempt_id))
        ids = attempt.question_ids or []
        by_id = Question.objects.prefetch_related(
            Prefetch("options", queryset=Option.objects.order_by("letter"))
        ).in_bulk(ids)
        questions = [by_id[qid] for qid in ids if qid in by_id]
        answers = {
            a.question.number: a.option.letter
            for a in attempt.answers.select_related("question", "option").filter(question_id__in=ids)
        }
        return Response(
            {
                "attempt_id": str(attempt.id),
                "status": attempt.status,
                "stage": services.stage_payload(attempt),
                "full_name": attempt.participant.full_name,
                "language": attempt.participant.language,
                "started_at": attempt.started_at,
                "expires_at": attempt.expires_at,
                "server_time": timezone.now(),
                "questions": QuestionPublicSerializer(questions, many=True).data,
                "answers": answers,
            }
        )


class AttemptAnswerView(AttemptAccessMixin, APIView):
    throttle_scope = "answer"

    @extend_schema(summary="Javobni saqlash (letter: null – javobni bekor qilish)", request=AnswerSerializer, parameters=[TOKEN_PARAM])
    def put(self, request, attempt_id, number):
        serializer = AnswerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        letter = serializer.validated_data["letter"]

        with transaction.atomic():
            attempt = self.get_attempt(request, attempt_id, for_update=True)
            if not attempt.is_open:
                return error("attempt_closed", status.HTTP_409_CONFLICT, status=attempt.status)
            if services.is_expired(attempt, grace_seconds=settings.ANSWER_GRACE_SECONDS):
                transaction.on_commit(lambda: services.expire_if_needed(attempt))
                return error("attempt_expired", status.HTTP_409_CONFLICT, status=Attempt.Status.EXPIRED)

            ids = attempt.question_ids or []
            question = get_object_or_404(Question, number=number, id__in=ids)
            if letter is None:
                Answer.objects.filter(attempt=attempt, question=question).delete()
            else:
                option = get_object_or_404(Option, question=question, letter=letter)
                Answer.objects.update_or_create(attempt=attempt, question=question, defaults={"option": option})
            answered = attempt.answers.filter(question_id__in=ids).count()

        return Response({"number": number, "letter": letter, "answered_count": answered})


class AttemptFinishView(AttemptAccessMixin, APIView):
    @extend_schema(summary="Testni yakunlash va natijani hisoblash", request=None, parameters=[TOKEN_PARAM])
    def post(self, request, attempt_id):
        attempt = self.get_attempt(request, attempt_id)
        if attempt.is_open:
            expired = services.is_expired(attempt, grace_seconds=settings.ANSWER_GRACE_SECONDS)
            attempt = services.finalize(
                attempt, status=Attempt.Status.EXPIRED if expired else Attempt.Status.FINISHED
            )
        return Response(services.result_payload(attempt))


class AttemptResultView(AttemptAccessMixin, APIView):
    @extend_schema(summary="Natija", parameters=[TOKEN_PARAM])
    def get(self, request, attempt_id):
        attempt = services.expire_if_needed(self.get_attempt(request, attempt_id))
        if attempt.is_open:
            return error("attempt_in_progress", status.HTTP_409_CONFLICT, expires_at=attempt.expires_at)
        return Response(services.result_payload(attempt))


class AttemptCertificateView(AttemptAccessMixin, APIView):
    @extend_schema(
        summary="Sertifikat (PDF)",
        parameters=[
            OpenApiParameter("token", str, OpenApiParameter.QUERY, required=True),
            OpenApiParameter("lang", str, OpenApiParameter.QUERY, enum=LANG_CODES),
        ],
        responses={(200, "application/pdf"): bytes},
    )
    def get(self, request, attempt_id):
        attempt = services.expire_if_needed(self.get_attempt(request, attempt_id))
        if attempt.is_open:
            return error("attempt_in_progress", status.HTTP_409_CONFLICT)
        if not attempt.has_certificate:
            return error("certificate_not_available", status.HTTP_403_FORBIDDEN)
        lang = request.query_params.get("lang") or attempt.participant.language
        if lang not in LANG_CODES:
            lang = "uz"
        pdf = render_certificate(services.result_payload(attempt), lang)
        response = HttpResponse(pdf, content_type="application/pdf")
        filename = f"certificate-{str(attempt.id)[:8]}.pdf"
        disposition = "inline" if request.query_params.get("inline") else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        response["Cache-Control"] = "private, no-store"
        return response


class TelegramAuthView(APIView):
    throttle_scope = "telegram"

    @extend_schema(summary="Telegram initData ni tekshirish", request=TelegramAuthSerializer)
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = validate_init_data(serializer.validated_data["init_data"])
        except TelegramAuthError as exc:
            return error("telegram_auth_failed", status.HTTP_403_FORBIDDEN, detail=str(exc))
        full_name = " ".join(filter(None, [user.get("first_name"), user.get("last_name")])).strip()
        return Response(
            {
                "ok": True,
                "user": {
                    "id": user["id"],
                    "first_name": user.get("first_name", ""),
                    "last_name": user.get("last_name", ""),
                    "username": user.get("username", ""),
                    "language_code": user.get("language_code", ""),
                    "full_name": full_name,
                },
            }
        )


def attempt_summary(attempt, with_name=False):
    item = {
        "attempt_id": str(attempt.id),
        "token": attempt.token,
        "status": attempt.status,
        "stage": services.stage_payload(attempt),
        "started_at": attempt.started_at,
        "finished_at": attempt.finished_at,
        "total_score": attempt.total_score,
        "max_score": services.attempt_max_score(attempt),
        "percent": float(attempt.percent) if attempt.percent is not None else None,
        "level": services.level_payload(attempt.level),
    }
    if with_name:
        item["full_name"] = attempt.participant.full_name
    return item


class BotAccessMixin:
    """Faqat bot servisi uchun: `X-Bot-Token` = TELEGRAM_BOT_TOKEN (nginx /api/v1/bot/ ni tashqariga yopadi)."""

    def bot_forbidden(self, request):
        token = settings.TELEGRAM_BOT_TOKEN
        given = request.headers.get("X-Bot-Token", "")
        if not token or not hmac.compare_digest(given.encode(), token.encode()):
            return error("forbidden", status.HTTP_403_FORBIDDEN)
        return None


class BotResultsView(BotAccessMixin, APIView):
    """Telegram foydalanuvchisining so‘nggi natijalari (bot uchun)."""

    @extend_schema(exclude=True)
    def get(self, request):
        if denied := self.bot_forbidden(request):
            return denied
        try:
            telegram_id = int(request.query_params.get("telegram_id", ""))
        except ValueError:
            return error("telegram_id_required", status.HTTP_400_BAD_REQUEST)

        attempts = (
            Attempt.objects.filter(participant__telegram_id=telegram_id)
            .select_related("participant", "level", "stage")
            .order_by("-started_at")[:5]
        )
        items = [attempt_summary(services.expire_if_needed(a)) for a in attempts]
        return Response({"attempts": items})


class BotRegisterView(BotAccessMixin, APIView):
    """Bot /start: foydalanuvchini yozadi (referal bilan) va bosqichlar holatini qaytaradi."""

    @extend_schema(exclude=True)
    def post(self, request):
        if denied := self.bot_forbidden(request):
            return denied
        serializer = BotRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        is_new = not TelegramAccount.objects.filter(telegram_id=data["id"]).exists()
        account = upsert_account(data)
        if is_new:
            progress.attach_referrer(account, progress.parse_referral(data.get("start_param")))
        return Response(self._payload(account))

    @staticmethod
    def _payload(account):
        return {"language": progress.account_language(account), **progress.progress(account)}


class BotProgressView(BotAccessMixin, APIView):
    """Bot: obunani qayta tekshirish va bosqichlar holati."""

    @extend_schema(exclude=True)
    def get(self, request):
        if denied := self.bot_forbidden(request):
            return denied
        try:
            telegram_id = int(request.query_params.get("telegram_id", ""))
        except ValueError:
            return error("telegram_id_required", status.HTTP_400_BAD_REQUEST)
        account = TelegramAccount.objects.filter(telegram_id=telegram_id).first()
        if account is None:
            return error("not_found", status.HTTP_404_NOT_FOUND)
        return Response(BotRegisterView._payload(account))


class BotLanguageView(BotAccessMixin, APIView):
    """Bot: foydalanuvchi tanlagan tilni saqlash."""

    @extend_schema(exclude=True)
    def post(self, request):
        if denied := self.bot_forbidden(request):
            return denied
        serializer = BotLanguageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        updated = TelegramAccount.objects.filter(telegram_id=data["telegram_id"]).update(bot_language=data["language"])
        if not updated:
            return error("not_found", status.HTTP_404_NOT_FOUND)
        return Response({"language": data["language"]})


class ProgressView(APIView):
    """Sayt/Mini App: bosqichlar, kanallar va takliflar holati (Bearer token)."""

    @extend_schema(summary="Bosqichlar holati (Bearer token)")
    def get(self, request):
        account = account_from_request(request)
        if account is None:
            return error("unauthorized", status.HTTP_401_UNAUTHORIZED)
        return Response(progress.progress(account))


def auth_response(account):
    return Response({"token": issue_token(account), "user": account_payload(account)})


class AuthWidgetView(APIView):
    """Veb: Telegram Login Widget ma’lumoti → sessiya tokeni."""

    throttle_scope = "auth"

    @extend_schema(summary="Telegram Login Widget orqali kirish", request=None)
    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        try:
            user = validate_widget_data(data)
        except TelegramAuthError as exc:
            return error("telegram_auth_failed", status.HTTP_403_FORBIDDEN, detail=str(exc))
        return auth_response(upsert_account(user))


class AuthWebAppView(APIView):
    """Mini App: initData → sessiya tokeni."""

    throttle_scope = "auth"

    @extend_schema(summary="Telegram Mini App orqali kirish", request=TelegramAuthSerializer)
    def post(self, request):
        serializer = TelegramAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            account = account_from_init_data(serializer.validated_data["init_data"])
        except TelegramAuthError as exc:
            return error("telegram_auth_failed", status.HTTP_403_FORBIDDEN, detail=str(exc))
        return auth_response(account)


class AuthMeView(APIView):
    @extend_schema(summary="Joriy foydalanuvchi (Bearer token)")
    def get(self, request):
        account = account_from_request(request)
        if account is None:
            return error("unauthorized", status.HTTP_401_UNAUTHORIZED)
        return Response({"user": account_payload(account)})


class MyAttemptsView(APIView):
    @extend_schema(summary="Foydalanuvchining urinishlari (Bearer token)")
    def get(self, request):
        account = account_from_request(request)
        if account is None:
            return error("unauthorized", status.HTTP_401_UNAUTHORIZED)
        attempts = (
            Attempt.objects.filter(participant__telegram_id=account.telegram_id)
            .select_related("participant", "level", "stage")
            .order_by("-started_at")[:30]
        )
        items = [attempt_summary(services.expire_if_needed(a), with_name=True) for a in attempts]
        return Response({"attempts": items})


class VerifyView(APIView):
    """Ochiq: sertifikat haqiqiyligini tekshirish (QR kod). Ma’lumot bazadan olinadi, PDF’dan emas."""

    throttle_scope = "verify"

    @extend_schema(summary="Sertifikatni tekshirish (tekshiruv kodi bo‘yicha)")
    def get(self, request, code):
        normalized = normalize_verify_code(code)
        attempt = (
            Attempt.objects.select_related("participant", "level", "stage")
            .filter(verify_code=normalized)
            .exclude(status=Attempt.Status.IN_PROGRESS)
            .first()
            if normalized
            else None
        )
        # Sertifikatsiz bosqich urinishlari sertifikat sifatida tasdiqlanmaydi
        if attempt is None or not attempt.has_certificate:
            return error("certificate_not_found", status.HTTP_404_NOT_FOUND, valid=False)
        return Response(
            {
                "valid": True,
                "code": format_verify_code(attempt.verify_code),
                "full_name": attempt.participant.full_name,
                "finished_at": attempt.finished_at,
                "total_score": attempt.total_score,
                "max_score": services.attempt_max_score(attempt),
                "percent": float(attempt.percent or 0),
                "stage": services.stage_payload(attempt),
                "level": services.level_payload(attempt.level),
                "telegram_verified": bool(attempt.participant.telegram_id),
            }
        )
