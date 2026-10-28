"""API serializerlari.

DIQQAT: bu yerdagi savol/variant serializerlarida `points`, `correct`, `reason_*`, `logic_*`
maydonlari hech qachon bo‘lmasligi kerak (tests/test_no_leak.py tekshiradi).
"""

import re

from rest_framework import serializers

from ..models import LETTERS, Language, Option, Question

PHONE_RE = re.compile(r"^\+998\d{9}$")


class OptionPublicSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = Option
        fields = ["letter", "value", "image"]

    def get_image(self, obj):
        return obj.image.url if obj.image else None


class QuestionPublicSerializer(serializers.ModelSerializer):
    figure = serializers.SerializerMethodField()
    prompt = serializers.SerializerMethodField()
    options = OptionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["number", "type", "prompt", "figure", "options"]

    def get_figure(self, obj):
        return obj.figure.url if obj.figure else None

    def get_prompt(self, obj):
        return {"uz": obj.prompt_uz, "ru": obj.prompt_ru, "en": obj.prompt_en or obj.prompt_uz}


class AttemptCreateSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=120, trim_whitespace=True)
    phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    language = serializers.ChoiceField(choices=Language.choices, default=Language.UZ)
    telegram_init_data = serializers.CharField(required=False, allow_blank=True, default="", max_length=4096)
    stage = serializers.IntegerField(min_value=1, default=1)

    def validate_full_name(self, value):
        value = re.sub(r"\s+", " ", value).strip()
        if len(value) < 2:
            raise serializers.ValidationError("too_short")
        return value

    def validate_phone(self, value):
        if not value:
            return ""
        normalized = re.sub(r"[\s\-()]", "", value)
        if not PHONE_RE.match(normalized):
            raise serializers.ValidationError("invalid_phone")
        return normalized


class AnswerSerializer(serializers.Serializer):
    letter = serializers.ChoiceField(choices=[(x, x) for x in LETTERS], allow_null=True)


class TelegramAuthSerializer(serializers.Serializer):
    init_data = serializers.CharField(max_length=4096)


class BotRegisterSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    first_name = serializers.CharField(required=False, allow_blank=True, default="", max_length=256)
    last_name = serializers.CharField(required=False, allow_blank=True, default="", max_length=256)
    username = serializers.CharField(required=False, allow_blank=True, default="", max_length=64)
    language_code = serializers.CharField(required=False, allow_blank=True, default="", max_length=12)
    start_param = serializers.CharField(required=False, allow_blank=True, default="", max_length=64)


class BotLanguageSerializer(serializers.Serializer):
    telegram_id = serializers.IntegerField()
    language = serializers.ChoiceField(choices=Language.choices)
