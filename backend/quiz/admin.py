from django.contrib import admin, messages
from django.core.exceptions import ValidationError
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
    ScoreLevel,
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
    list_display = ["number", "thumb", "prompt_uz", "type", "category", "order", "is_active", "correct_letter"]
    list_display_links = ["number", "thumb"]
    list_editable = ["order", "is_active"]
    list_filter = ["category", "type", "is_active"]
    search_fields = ["prompt_uz", "prompt_ru", "logic_uz"]
    ordering = ["order", "number"]
    inlines = [OptionInline]
    readonly_fields = ["figure_preview"]
    fieldsets = [
        (None, {"fields": ["number", "order", "is_active", "type", "category"]}),
        ("Savol matni", {"fields": ["prompt_uz", "prompt_ru"]}),
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
    list_display = ["name_uz", "name_ru", "min_score", "max_score", "attempts_count"]
    list_editable = ["min_score", "max_score"]
    ordering = ["min_score"]

    @display(description="Urinishlar")
    def attempts_count(self, obj):
        return obj.attempts.count()


@admin.register(TestSettings)
class TestSettingsAdmin(ModelAdmin):
    list_display = ["__str__"]

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
        "participant_phone",
        "language",
        "status_badge",
        "started_at",
        "finished_at",
        "score_display",
        "percent",
        "level",
    ]
    list_filter = [
        ("status", ChoicesDropdownFilter),
        ("level", RelatedDropdownFilter),
        ("participant__language", ChoicesDropdownFilter),
        ("started_at", RangeDateFilter),
    ]
    list_filter_submit = True
    search_fields = ["participant__full_name", "participant__phone", "id"]
    date_hierarchy = "started_at"
    inlines = [AnswerInline]
    actions = ["export_selected_csv", "export_selected_xlsx"]
    actions_list = ["export_all_csv", "export_all_xlsx", "open_stats"]
    readonly_fields = [
        "id",
        "participant",
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
        (None, {"fields": ["id", "participant", "status"]}),
        ("Vaqt", {"fields": ["started_at", "expires_at", "finished_at"]}),
        ("Natija", {"fields": ["total_score", "percent", "level", "category_summary"]}),
    ]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("participant", "level")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @display(description="Ishtirokchi", ordering="participant__full_name")
    def participant_name(self, obj):
        return obj.participant.full_name

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
    list_display = ["telegram_id", "full_name", "username", "language_code", "created_at", "last_login"]
    search_fields = ["telegram_id", "first_name", "last_name", "username"]
    list_filter = [("last_login", RangeDateFilter)]
    list_filter_submit = True
    readonly_fields = ["telegram_id", "first_name", "last_name", "username", "photo_url", "language_code", "created_at", "last_login"]

    def has_add_permission(self, request):
        return False
