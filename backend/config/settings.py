"""Django sozlamalari. Barcha qiymatlar muhit o‘zgaruvchilaridan (.env) olinadi."""

import os
from pathlib import Path

from django.urls import reverse_lazy

BASE_DIR = Path(__file__).resolve().parent.parent


def env(name, default=None):
    return os.environ.get(name, default)


def env_bool(name, default=False):
    return env(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    return [item.strip() for item in env(name, default).split(",") if item.strip()]


SECRET_KEY = env("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("DJANGO_SECRET_KEY muhit o‘zgaruvchisi berilmagan")

DEBUG = env_bool("DJANGO_DEBUG", False)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1")
PUBLIC_URL = env("PUBLIC_URL", "http://localhost").rstrip("/")
# PUBLIC_URL domeni (masalan, Telegram uchun HTTPS tunnel) avtomatik ruxsat etiladi
_public_host = PUBLIC_URL.split("://", 1)[-1].split("/", 1)[0].split(":", 1)[0]
if _public_host and _public_host not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_public_host)

# Cloudflare quick tunnel (docker compose --profile tunnel): HTTPS manzil avtomatik aniqlanadi
TUNNEL_METRICS_URL = env("TUNNEL_METRICS_URL", "").rstrip("/")
if TUNNEL_METRICS_URL:
    ALLOWED_HOSTS.append(".trycloudflare.com")

CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS", PUBLIC_URL)
if TUNNEL_METRICS_URL:
    CSRF_TRUSTED_ORIGINS.append("https://*.trycloudflare.com")
CORS_ALLOWED_ORIGINS = env_list("DJANGO_CORS_ALLOWED_ORIGINS", PUBLIC_URL)
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "x-attempt-token",
    "x-requested-with",
)

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "drf_spectacular",
    "quiz",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", "iqtest"),
        "USER": env("POSTGRES_USER", "iqtest"),
        "PASSWORD": env("POSTGRES_PASSWORD", ""),
        "HOST": env("POSTGRES_HOST", "db"),
        "PORT": env("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "uz"
LANGUAGES = [("uz", "O‘zbekcha"), ("ru", "Русский")]
TIME_ZONE = env("TIME_ZONE", "Asia/Tashkent")
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = Path(env("STATIC_ROOT", "/vol/static"))
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(env("MEDIA_ROOT", "/vol/media"))

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Nginx ortida ishlash
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env("THROTTLE_ANON", "600/min"),
        "attempt_create": env("THROTTLE_ATTEMPT_CREATE", "30/hour"),
        "answer": env("THROTTLE_ANSWER", "240/min"),
        "telegram": env("THROTTLE_TELEGRAM", "60/min"),
        "auth": env("THROTTLE_AUTH", "30/min"),
        "verify": env("THROTTLE_VERIFY", "60/min"),
    },
    "NUM_PROXIES": int(env("NUM_PROXIES", "1")),
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Mantiqiy test API",
    "DESCRIPTION": "IQ test platformasi API. Ballar va to‘g‘ri javoblar hech qachon qaytarilmaydi.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# Test sozlamalari
TEST_DURATION_MINUTES = int(env("TEST_DURATION_MINUTES", "40"))
ANSWER_GRACE_SECONDS = int(env("ANSWER_GRACE_SECONDS", "3"))
TELEGRAM_BOT_TOKEN = env("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_BOT_USERNAME = env("TELEGRAM_BOT_USERNAME", "")
TELEGRAM_API_BASE = env("TELEGRAM_API_BASE", "https://api.telegram.org").rstrip("/")
# Mini App orqali topshirilgan test natijasini bot chatiga yuborish
TELEGRAM_NOTIFY_RESULTS = env_bool("TELEGRAM_NOTIFY_RESULTS", True)
TELEGRAM_AUTH_MAX_AGE = int(env("TELEGRAM_AUTH_MAX_AGE", "86400"))
# Saytga kirish faqat Telegram orqali (bot token bo‘lmasa avtomatik o‘chadi)
REQUIRE_TELEGRAM_AUTH = env_bool("REQUIRE_TELEGRAM_AUTH", True) and bool(TELEGRAM_BOT_TOKEN)
AUTH_SESSION_DAYS = int(env("AUTH_SESSION_DAYS", "30"))

UNFOLD = {
    "SITE_TITLE": "Mantiqiy test",
    "SITE_HEADER": "Mantiqiy test",
    "SITE_SYMBOL": "psychology",
    "SHOW_HISTORY": True,
    "DASHBOARD_CALLBACK": "quiz.stats.dashboard_callback",
    "COLORS": {
        "primary": {
            "50": "253 241 236",
            "100": "251 222 212",
            "200": "246 189 170",
            "300": "240 150 120",
            "400": "234 110 76",
            "500": "228 87 46",
            "600": "205 72 33",
            "700": "170 58 27",
            "800": "137 48 24",
            "900": "112 41 22",
            "950": "61 19 9",
        },
    },
    "SIDEBAR": {
        "show_search": False,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Tahlil",
                "items": [
                    {"title": "Statistika", "icon": "monitoring", "link": reverse_lazy("admin:quiz_stats")},
                    {"title": "Urinishlar", "icon": "assignment", "link": reverse_lazy("admin:quiz_attempt_changelist")},
                    {"title": "Ishtirokchilar", "icon": "group", "link": reverse_lazy("admin:quiz_participant_changelist")},
                    {"title": "Telegram foydalanuvchilar", "icon": "send", "link": reverse_lazy("admin:quiz_telegramaccount_changelist")},
                ],
            },
            {
                "title": "Test",
                "items": [
                    {"title": "Savollar", "icon": "quiz", "link": reverse_lazy("admin:quiz_question_changelist")},
                    {"title": "Darajalar", "icon": "military_tech", "link": reverse_lazy("admin:quiz_scorelevel_changelist")},
                    {"title": "Sozlamalar", "icon": "settings", "link": reverse_lazy("admin:quiz_testsettings_changelist")},
                ],
            },
            {
                "title": "Tizim",
                "items": [
                    {"title": "Administratorlar", "icon": "admin_panel_settings", "link": reverse_lazy("admin:auth_user_changelist")},
                    {"title": "API hujjati", "icon": "api", "link": "/api/docs"},
                ],
            },
        ],
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", "INFO")},
}
