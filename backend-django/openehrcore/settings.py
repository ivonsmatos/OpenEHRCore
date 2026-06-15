"""
Django settings for openehrcore project.
"""

from pathlib import Path
import os
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config(
    "DJANGO_SECRET_KEY", default="django-insecure-dev-key-change-in-production"
)

# SECURITY WARNING: don't run with debug turned on in production!
# SECURITY FIX: DEBUG agora é False por padrão
DEBUG = config("DEBUG", default=False, cast=bool)

ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="localhost,127.0.0.1,45.151.122.234,api.grephub.com.br,app.grephub.com.br,grephub.com.br,farmedtech.com.br",
).split(",")

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "fhir_api",
    "transcription",
    "core",
]

# =====================================================
# AI Configuration (open-source / self-hosted, API compatível com OpenAI)
# Os dados permanecem no seu ambiente (sem transferência internacional — LGPD).
# Produção: vLLM (GPU no Brasil/on-prem). Dev: Ollama. Config em core/services/llm_client.py
# =====================================================
LLM_BASE_URL = config('LLM_BASE_URL', default='http://localhost:11434/v1')
LLM_MODEL = config('LLM_MODEL', default='qwen2.5:7b-instruct')
LLM_VISION_MODEL = config('LLM_VISION_MODEL', default='qwen2.5vl:7b')
ASR_BASE_URL = config('ASR_BASE_URL', default='http://localhost:8001/v1')
ASR_MODEL = config('ASR_MODEL', default='Systran/faster-whisper-large-v3')
# Compatibilidade (config Ollama legada — serviços migrados usam LLM_* via llm_client)
OLLAMA_BASE_URL = config("OLLAMA_BASE_URL", default="http://localhost:11434")
OLLAMA_MODEL = config("OLLAMA_MODEL", default="mistral-nemo")
OLLAMA_URL = f"{OLLAMA_BASE_URL}/api/generate"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "fhir_api.middleware.rate_limit.RateLimitMiddleware",  # Sprint 22: Rate Limiting
    "fhir_api.middleware.role_access.RoleAccessMiddleware",  # RBAC por papel (QA)
]

ROOT_URLCONF = "openehrcore.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "openehrcore.wsgi.application"

# Database
# Produção: defina DATABASE_URL (postgres://...) ou as variáveis DB_*.
# Desenvolvimento/local: cai para SQLite quando nada é configurado.
DATABASE_URL = config('DATABASE_URL', default='')
if DATABASE_URL:
    import dj_database_url
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
elif config('DB_NAME', default=''):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER', default='postgres'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 600,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# REST Framework
# SECURITY FIX: Autenticação reativada
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "fhir_api.exception_handler.api_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "fhir_api.authentication.KeycloakAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # Throttling: protege contra brute-force/abuso (Sprint QA)
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': config('THROTTLE_ANON', default='30/minute'),
        'user': config('THROTTLE_USER', default='1000/hour'),
    },
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://localhost:3000,https://api.grephub.com.br,https://app.grephub.com.br,https://grephub.com.br",
).split(",")
CORS_ALLOW_CREDENTIALS = True

# FHIR Server Configuration
FHIR_SERVER_URL = config("FHIR_SERVER_URL", default="http://localhost:8080/fhir")
FHIR_SERVER_TIMEOUT = config("FHIR_SERVER_TIMEOUT", default=30, cast=int)

# Keycloak Configuration
KEYCLOAK_URL = config("KEYCLOAK_URL", default="http://localhost:8180")
KEYCLOAK_REALM = config("KEYCLOAK_REALM", default="openehrcore")
KEYCLOAK_CLIENT_ID = config("KEYCLOAK_CLIENT_ID", default="openehrcore")
KEYCLOAK_CLIENT_SECRET = config("KEYCLOAK_CLIENT_SECRET", default="")

# Validação adicional de tokens JWT (hardening — habilite em produção).
# Audience: por padrão o access token do Keycloak usa aud=account, por isso
# a verificação fica desligada até que KEYCLOAK_AUDIENCE seja definido.
KEYCLOAK_AUDIENCE = config('KEYCLOAK_AUDIENCE', default='')
# Issuer: habilite quando a KEYCLOAK_URL do backend == issuer do token.
KEYCLOAK_VERIFY_ISSUER = config('KEYCLOAK_VERIFY_ISSUER', default=False, cast=bool)
KEYCLOAK_ISSUER = config('KEYCLOAK_ISSUER', default='')

# Logging - JSON Estruturado para Produção
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
        "json": {
            "()": "fhir_api.logging.JsonFormatter",
        },
    },
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "verbose" if DEBUG else "json",
        },
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "openehrcore.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 5,
            "formatter": "json",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "errors.log"),
            "maxBytes": 10 * 1024 * 1024,  # 10 MB
            "backupCount": 10,
            "formatter": "json",
        },
        "audit": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "audit.log"),
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 20,
            "formatter": "json",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["console", "file_error"],
            "level": "ERROR",
            "propagate": False,
        },
        "fhir_api": {
            "handlers": ["console", "file"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
        "fhir_api.audit": {
            "handlers": ["audit"],
            "level": "INFO",
            "propagate": False,
        },
        "fhir_api.security": {
            "handlers": ["console", "file", "file_error"],
            "level": "WARNING",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "INFO",
    },
}

# Rate Limiting Configuration (Sprint 22)
RATE_LIMIT_ENABLED = config('RATE_LIMIT_ENABLED', default=True, cast=bool)

# =====================================================
# Security Hardening (produção — aplicado quando DEBUG=False)
# =====================================================
if not DEBUG:
    SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    X_FRAME_OPTIONS = 'DENY'
    CSRF_TRUSTED_ORIGINS = config(
        'CSRF_TRUSTED_ORIGINS',
        default='https://app.grephub.com.br,https://grephub.com.br,https://api.grephub.com.br'
    ).split(',')
