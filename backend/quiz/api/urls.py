from django.urls import path

from . import views

urlpatterns = [
    path("test/meta", views.TestMetaView.as_view(), name="test-meta"),
    path("attempts", views.AttemptCreateView.as_view(), name="attempt-create"),
    path("attempts/<uuid:attempt_id>/questions", views.AttemptQuestionsView.as_view(), name="attempt-questions"),
    path(
        "attempts/<uuid:attempt_id>/answers/<int:number>",
        views.AttemptAnswerView.as_view(),
        name="attempt-answer",
    ),
    path("attempts/<uuid:attempt_id>/finish", views.AttemptFinishView.as_view(), name="attempt-finish"),
    path("attempts/<uuid:attempt_id>/result", views.AttemptResultView.as_view(), name="attempt-result"),
    path(
        "attempts/<uuid:attempt_id>/certificate.pdf",
        views.AttemptCertificateView.as_view(),
        name="attempt-certificate",
    ),
    path("telegram/auth", views.TelegramAuthView.as_view(), name="telegram-auth"),
    path("bot/results", views.BotResultsView.as_view(), name="bot-results"),
    path("bot/register", views.BotRegisterView.as_view(), name="bot-register"),
    path("bot/progress", views.BotProgressView.as_view(), name="bot-progress"),
    path("bot/language", views.BotLanguageView.as_view(), name="bot-language"),
    path("auth/telegram/widget", views.AuthWidgetView.as_view(), name="auth-widget"),
    path("auth/telegram/webapp", views.AuthWebAppView.as_view(), name="auth-webapp"),
    path("auth/me", views.AuthMeView.as_view(), name="auth-me"),
    path("me/attempts", views.MyAttemptsView.as_view(), name="my-attempts"),
    path("me/progress", views.ProgressView.as_view(), name="my-progress"),
    path("verify/<str:code>", views.VerifyView.as_view(), name="verify"),
]
