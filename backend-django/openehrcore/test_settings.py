from .settings import *  # noqa: F401,F403

# Override Database to use in-memory SQLite for speed and to avoid file locks
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable Celery eagerly
CELERY_TASK_ALWAYS_EAGER = True

# Disable caches
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Simplify password hashing for speed
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use the test-only bypass authentication so the suite does not depend on a
# live Keycloak server. NUNCA usado em produção. Throttling é desligado em
# testes (não faz sentido com usuários mockados e gera ruído de cache).
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'openehrcore.test_auth.TestBypassAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}

# Desligar rate limiting durante os testes
RATE_LIMIT_ENABLED = False

# Timeout curto por padrão: testes que tocam FHIR/Keycloak reais (sem mock)
# falham rápido em vez de travar 30s cada (endereços inalcançáveis em CI).
# Sobrescreva com FHIR_SERVER_TIMEOUT=30 ao rodar contra a stack Docker.
FHIR_SERVER_TIMEOUT = config('FHIR_SERVER_TIMEOUT', default=1, cast=int)

# O hardening de produção é ativado quando DEBUG=False; nos testes o cliente usa
# http://testserver, então desligamos o redirect HTTPS para não gerar 301.
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
