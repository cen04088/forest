import os
from importlib.util import find_spec
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR.parent / "frontend" / "dist"


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=None):
    value = os.environ.get(name, "")
    if not value:
        return list(default or [])
    return [item.strip() for item in value.split(",") if item.strip()]


SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-only-forestrx-secret-key")
DEBUG = env_bool("DJANGO_DEBUG", default=True)

ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", ["localhost", "127.0.0.1", ".railway.app", ".up.railway.app"])
if railway_domain := os.environ.get("RAILWAY_PUBLIC_DOMAIN"):
    ALLOWED_HOSTS.append(railway_domain)

CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS")
if railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f"https://{railway_domain}")

CORS_ALLOWED_ORIGINS = env_list("CORS_ALLOWED_ORIGINS", ["http://127.0.0.1:5173", "http://localhost:5173"])
HAS_WHITENOISE = find_spec("whitenoise") is not None

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "recommendations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "recommendations.middleware.DevCorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
if HAS_WHITENOISE:
    MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "forestrx.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [FRONTEND_DIST_DIR],
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

WSGI_APPLICATION = "forestrx.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

# 정적 파일: STATIC_ROOT와 STATICFILES_DIRS가 겨치면 안 됨
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# frontend/dist/assets 만 정적 파일로 등록 (겹치기 방지)
_FRONTEND_ASSETS_DIR = FRONTEND_DIST_DIR / "assets"
STATICFILES_DIRS = [_FRONTEND_ASSETS_DIR] if _FRONTEND_ASSETS_DIR.exists() else []

if HAS_WHITENOISE:
    STORAGES = {
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
    # whitenoise가 SPA index.html을 fallback으로 서빙하도록 설정
    WHITENOISE_INDEX_FILE = True
    WHITENOISE_ROOT = str(FRONTEND_DIST_DIR)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
