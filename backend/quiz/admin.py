from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db.models import OuterRef, Q, Subquery
from django.forms.models import BaseInlineFormSet
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateFilter, RelatedDropdownFilter
from unfold.decorators import action, display

from . import exports
from .models import (
    LETTERS,
    MAX_POINTS,
    MIN_POINTS,
    Answer,
    Attempt,
    Option,
    Participant,
    Question,
    RequiredChannel,
    ScoreLevel,
    Stage,
    TelegramAccount,
    TestSettings,
)
from .stats import collect_stats


# --- Savollar -----------------------------------------------------------------


class OptionInlineFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return
        rows = [f.cleaned_data for f in self.forms if f.cleaned_data and not f.cleaned_data.get("DELETE")]
        letters = sorted(r["letter"] for r in rows)
        if letters != LETTERS:
            raise ValidationError("Savolda aniq 6 ta variant (A–F) bo‘lishi kerak.")
        for r in rows:
            if not MIN_POINTS <= r["points"] <= MAX_POINTS:
                raise ValidationError("Variant bali 3–7 oralig‘ida bo‘lishi kerak.")
        if sum(1 for r in rows if r["points"] == MAX_POINTS) != 1:
            raise ValidationError("Savolda aniq bitta 7 ballik variant bo‘lishi kerak.")


class OptionInline(TabularInline):
    model = Option
    formset = OptionInlineFormSet
    fields = ["letter", "value", "image", "preview", "points", "reason_uz"]
    readonly_fields = ["preview"]
    max_num = 6
    min_num = 6
    can_delete = False
    ordering = ["letter"]

    def get_extra(self, request, obj=None, **kwargs):
        return 0

    @display(description="Ko‘rinish")
    def preview(self, obj):
        if obj and obj.image:
            return format_html(
                '<img src="{}" style="height:56px;background:#fff;border:1px solid #D6D0C4;border-radius:8px;padding:4px">',
                obj.image.url,
            )
        if obj and obj.value is not None:
            return format_html('<strong style="font-size:18px">{}</strong>', obj.value)
        return "—"


@admin.register(Question)
class QuestionAdmin(ModelAdmin):
    list_display = ["number", "thumb", "prompt_uz", "type", "category", "difficulty", "order", "is_active", "correct_letter"]
    list_display_links = ["number", "thumb"]
    list_editable = ["difficulty", "order", "is_active"]
    list_filter = ["difficulty", "category", "type", "is_active"]
    search_fields = ["prompt_uz", "prompt_ru", "logic_uz"]
    ordering = ["order", "number"]
    inlines = [OptionInline]
    readonly_fields = ["figure_preview"]
    fieldsets = [
        (None, {"fields": ["number", "order", "is_active", "type", "category", "difficulty"]}),
        ("Savol matni", {"fields": ["prompt_uz", "prompt_ru", "prompt_en"]}),
        ("Rasm", {"fields": ["figure", "figure_preview"]}),
        ("Mantiq izohi", {"fields": ["logic_uz", "logic_ru"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("options")

    @display(description="Rasm")
    def thumb(self, obj):
        if obj.figure:
            return format_html(
                '<img src="{}" style="height:40px;background:#fff;border-radius:6px;border:1px solid #D6D0C4;padding:2px">',
                obj.figure.url,
            )
        return "—"

    @display(description="To‘g‘ri")
    def correct_letter(self, obj):
        for o in obj.options.all():
            if o.points == MAX_POINTS:
                return o.letter
        return "—"

    @display(description="Ko‘rinish")
    def figure_preview(self, obj):
        if obj and obj.figure:
            return format_html(
                '<img src="{}" style="max-height:260px;background:#F4F1EA;border-radius:18px;padding:16px">',
                obj.figure.url,
            )
        return "—"

    def save_formset(self, request, form, formset, change):
        if formset.model is not Option:
            return super().save_formset(request, form, formset, change)
        instances = formset.save(commit=False)
        # Avval 7 ballik bo‘lmaganlar saqlanadi – "bitta 7" cheklovi vaqtincha buzilmasligi uchun
        instances.sort(key=lambda o: o.points == MAX_POINTS)
        for obj in instances:
            obj.save()
        formset.save_m2m()


# --- Darajalar va sozlamalar --------------------------------------------------


@admin.register(ScoreLevel)
class ScoreLevelAdmin(ModelAdmin):
    list_display = ["name_uz", "name_ru", "name_en", "min_percent", "max_percent", "attempts_count"]
    list_editable = ["min_percent", "max_percent"]
    ordering = ["min_percent"]

    @display(description="Urinishlar")
    def attempts_count(self, obj):
        return obj.attempts.count()


@admin.register(Stage)
class StageAdmin(ModelAdmin):
    list_display = [
        "number", "question_count", "duration_minutes", "max_difficulty", "friends_required", "certificate",
        "is_active", "attempts_count",
    ]
    list_editable = ["question_count", "duration_minutes", "max_difficulty", "friends_required", "certificate", "is_active"]
    ordering = ["number"]

    def has_delete_permission(self, request, obj=None):
        # Urinishlari bor bosqich o‘chirilmaydi (faqat nofaol qilinadi)
        return obj is None or not obj.attempts.exists()

    @display(description="Urinishlar")
    def attempts_count(self, obj):
        return obj.attempts.count()


@admin.register(RequiredChannel)
class RequiredChannelAdmin(ModelAdmin):
    list_display = ["title", "chat", "link", "is_active", "order", "bot_check"]
    list_editable = ["is_active", "order"]
    fields = ["title", "chat", "invite_link", "is_active", "order"]

    @display(description="Havola")
    def link(self, obj):
        return format_html('<a href="{0}" target="_blank" rel="noopener">{0}</a>', obj.url) if obj.url else "—"

    @display(description="Bot holati")
    def bot_check(self, obj):
        from .telegram import bot_api

        try:
            me = bot_api("getMe", timeout=4)
            member = bot_api("getChatMember", {"chat_id": obj.chat, "user_id": me["id"]}, timeout=4)
        except Exception as exc:
            return format_html('<span style="color:#E4572E">✗ {}</span>', str(exc)[:80])
        if member.get("status") == "administrator":
            return format_html('<span style="color:#2A7F8F">✓ bot admin</span>')
        return format_html('<span style="color:#E4572E">✗ bot admin emas</span>')


@admin.register(TestSettings)
class TestSettingsAdmin(ModelAdmin):
    list_display = ["__str__", "subscription_required"]

    def has_add_permission(self, request):
        return not TestSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj = TestSettings.load()
        return redirect(reverse("admin:quiz_testsettings_change", args=[obj.pk]))


# --- Ishtirokchilar va urinishlar ---------------------------------------------


class AnswerInline(TabularInline):
    model = Answer
    fields = ["question_number", "question_prompt", "chosen", "points", "answered_at"]
    readonly_fields = fields
    extra = 0
    can_delete = False
    ordering = ["question__order", "question__number"]

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("question", "option")

    @display(description="Savol")
    def question_number(self, obj):
        return obj.question.number

    @display(description="Matn")
    def question_prompt(self, obj):
        return obj.question.prompt_uz

    @display(description="Tanlangan")
    def chosen(self, obj):
        return obj.option.letter

    @display(description="Ball", label={"7": "success", "6": "info", "5": "warning", "4": "warning", "3": "danger"})
    def points(self, obj):
        return str(obj.option.points)


class AttemptInline(TabularInline):
    model = Attempt
    fields = ["started_at", "status", "total_score", "percent", "level"]
    readonly_fields = fields
    extra = 0
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Participant)
class ParticipantAdmin(ModelAdmin):
    list_display = ["full_name", "phone", "language", "telegram_id", "created_at", "attempts_count"]
    list_filter = ["language", ("created_at", RangeDateFilter)]
    list_filter_submit = True
    search_fields = ["full_name", "phone", "telegram_id"]
    inlines = [AttemptInline]

    @display(description="Urinishlar")
    def attempts_count(self, obj):
        return obj.attempts.count()


@admin.register(Attempt)
class AttemptAdmin(ModelAdmin):
    list_display = [
        "participant_name",
        "participant_telegram",
        "participant_phone",
        "language",
        "stage",
        "status_badge",
        "started_at",
        "finished_at",
        "score_display",
        "percent",
        "level",
    ]
    list_filter = [
        ("status", ChoicesDropdownFilter),
        ("stage", RelatedDropdownFilter),
        ("level", RelatedDropdownFilter),
        ("participant__language", ChoicesDropdownFilter),
        ("started_at", RangeDateFilter),
    ]
    list_filter_submit = True
    search_fields = ["participant__full_name", "participant__phone", "participant__telegram_id", "id", "verify_code"]
    date_hierarchy = "started_at"
    inlines = [AnswerInline]
    actions = ["export_selected_csv", "export_selected_xlsx"]
    actions_list = ["export_all_csv", "export_all_xlsx", "open_stats"]
    readonly_fields = [
        "id",
        "verify_code",
        "participant",
        "stage",
        "status",
        "started_at",
        "expires_at",
        "finished_at",
        "total_score",
        "percent",
        "level",
        "category_summary",
    ]
    fieldsets = [
        (None, {"fields": ["id", "participant", "stage", "status", "verify_code"]}),
        ("Vaqt", {"fields": ["started_at", "expires_at", "finished_at"]}),
        ("Natija", {"fields": ["total_score", "percent", "level", "category_summary"]}),
    ]

    def get_queryset(self, request):
        username = TelegramAccount.objects.filter(telegram_id=OuterRef("participant__telegram_id")).values("username")[:1]
        return super().get_queryset(request).select_related("participant", "level", "stage").annotate(tg_username=Subquery(username))

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Ishtirokchi", ordering="participant__full_name")
    def participant_name(self, obj):
        return obj.participant.full_name

    @display(description="Telegram", ordering="tg_username")
    def participant_telegram(self, obj):
        if obj.tg_username:
            return format_html('<a href="https://t.me/{0}" target="_blank" rel="noopener">@{0}</a>', obj.tg_username)
        return obj.participant.telegram_id or "—"

    @display(description="Telefon")
    def participant_phone(self, obj):
        return obj.participant.phone or "—"

    @display(description="Til", ordering="participant__language")
    def language(self, obj):
        return obj.participant.language.upper()

    @display(
        description="Holat",
        ordering="status",
        label={
            Attempt.Status.IN_PROGRESS: "info",
            Attempt.Status.FINISHED: "success",
            Attempt.Status.EXPIRED: "warning",
        },
    )
    def status_badge(self, obj):
        return obj.status, obj.get_status_display()

    @display(description="Ball", ordering="total_score")
    def score_display(self, obj):
        return "—" if obj.total_score is None else obj.total_score

    @display(description="Kategoriyalar")
    def category_summary(self, obj):
        from .models import CATEGORY_NAMES

        rows = []
        for key, names in CATEGORY_NAMES.items():
            data = (obj.category_scores or {}).get(key)
            if data:
                rows.append(f"{names['uz']}: {data['score']} / {data['max']} ({data['percent']}%)")
        return format_html("<br>".join(["{}"] * len(rows)), *rows) if rows else "—"

    @admin.action(description="Tanlanganlarni CSV ga eksport")
    def export_selected_csv(self, request, queryset):
        return exports.export_csv(queryset)

    @admin.action(description="Tanlanganlarni Excel ga eksport")
    def export_selected_xlsx(self, request, queryset):
        return exports.export_xlsx(queryset)

    @action(description="CSV eksport", url_path="export-csv")
    def export_all_csv(self, request):
        return exports.export_csv(self._filtered_queryset(request))

    @action(description="Excel eksport", url_path="export-xlsx")
    def export_all_xlsx(self, request):
        return exports.export_xlsx(self._filtered_queryset(request))

    @action(description="Statistika", url_path="stats-link")
    def open_stats(self, request):
        return redirect(reverse("admin:quiz_stats"))

    def _filtered_queryset(self, request):
        """Changelist dagi filtrlar (referer query string) bo‘yicha urinishlar."""
        from urllib.parse import urlparse

        from django.http import QueryDict

        referer = request.META.get("HTTP_REFERER", "")
        query = urlparse(referer).query if referer else ""
        original_get = request.GET
        try:
            request.GET = QueryDict(query)
            cl = self.get_changelist_instance(request)
            return cl.get_queryset(request)
        except Exception:
            return self.get_queryset(request)
        finally:
            request.GET = original_get

    def get_urls(self):
        custom = [
            path("stats/", self.admin_site.admin_view(self.stats_view), name="quiz_stats"),
        ]
        return custom + super().get_urls()

    def stats_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            "title": "Statistika",
            "stats": collect_stats(),
        }
        return TemplateResponse(request, "admin/quiz/stats.html", context)


@admin.register(TelegramAccount)
class TelegramAccountAdmin(ModelAdmin):
    list_display = [
        "telegram_id", "real_name", "telegram_name", "username_link", "language_code", "referred_by",
        "friends_count", "created_at", "last_login",
    ]
    list_display_links = ["telegram_id", "real_name"]
    search_fields = ["telegram_id", "real_name", "first_name", "last_name", "username"]
    fields = [
        "real_name", "telegram_id", "first_name", "last_name", "username", "photo_url", "language_code", "bot_language",
        "referred_by", "referral_confirmed_at", "created_at", "last_login",
    ]
    list_filter = [("last_login", RangeDateFilter)]
    list_filter_submit = True
    readonly_fields = [
        "telegram_id", "first_name", "last_name", "username", "photo_url", "language_code", "bot_language",
        "referred_by", "referral_confirmed_at", "created_at", "last_login",
    ]

    def get_queryset(self, request):
        from django.db.models import Count

        return (
            super().get_queryset(request)
            .select_related("referred_by")
            .annotate(friends=Count("referrals", filter=Q(referrals__referral_confirmed_at__isnull=False)))
        )

    @display(description="Taklif qilgan do‘stlar", ordering="friends")
    def friends_count(self, obj):
        return obj.friends

    def has_add_permission(self, request):
        return False

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if change and "real_name" in form.changed_data and obj.real_name:
            # Avvalgi natijalar va sertifikatlardagi ism ham tuzatiladi
            updated = Participant.objects.filter(telegram_id=obj.telegram_id).update(full_name=obj.real_name)
            self.message_user(request, f"Ism yangilandi: {updated} ta urinishdagi ism ham o‘zgartirildi.", messages.SUCCESS)

    @display(description="Telegram'dagi ism")
    def telegram_name(self, obj):
        return obj.full_name or "—"

    @display(description="Username")
    def username_link(self, obj):
        if not obj.username:
            return "—"
        return format_html('<a href="https://t.me/{0}" target="_blank" rel="noopener">@{0}</a>', obj.username)
