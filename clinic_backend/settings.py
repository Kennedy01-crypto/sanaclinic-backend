from datetime import timedelta
from pathlib import Path
import os
from urllib.parse import parse_qs, unquote, urlparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "True").lower() in {"1", "true", "yes", "on"}

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
if not ALLOWED_HOSTS or ALLOWED_HOSTS == [""]:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
CORS_ALLOWED_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",") if origin.strip()]
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'drf_spectacular',
    'accounts',
    'doctors',
    'appointments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'clinic_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'clinic_backend.wsgi.application'

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ImproperlyConfigured(
        'DATABASE_URL must be set. This project requires PostgreSQL.'
    )

database_url = urlparse(DATABASE_URL)
if database_url.scheme not in {'postgres', 'postgresql'}:
    raise ImproperlyConfigured('DATABASE_URL must use the postgres or postgresql scheme.')

database_query = parse_qs(database_url.query)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(database_url.path.lstrip('/')),
        'USER': unquote(database_url.username or ''),
        'PASSWORD': unquote(database_url.password or ''),
        'HOST': database_url.hostname,
        'PORT': database_url.port or '5432',
        'CONN_MAX_AGE': 60,
        'OPTIONS': {
            key: values[-1]
            for key, values in database_query.items()
        },
    }
}

if not all((DATABASES['default']['NAME'], DATABASES['default']['USER'], DATABASES['default']['HOST'])):
    raise ImproperlyConfigured('DATABASE_URL must include a database name, username, and host.')

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.User'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'clinic_backend.authentication.CookieJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/min',
        'user': '200/min',
    },
}

SIMPLE_JWT = {
    'AUTH_COOKIE': 'access_token',
    'AUTH_COOKIE_REFRESH': 'refresh_token',
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Clinic Booking API',
    'DESCRIPTION': 'Patient-facing and administrator clinic APIs. Operations are grouped by audience and category.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {'name': 'Patient - Accounts', 'description': 'Patient registration, sign-in, profile, and password endpoints. The token endpoint also issues tokens for staff administrators.'},
        {'name': 'Patient - Doctors', 'description': 'Browse active clinic doctors and their specialties.'},
        {'name': 'Patient - Slots', 'description': 'View scheduled 30-minute appointment slots and their availability.'},
        {'name': 'Patient - Appointments', 'description': 'Book, review, reschedule, and cancel the signed-in patient’s appointments.'},
        {'name': 'Admin - Dashboard', 'description': 'Staff-only clinic overview and operational summary.'},
        {'name': 'Admin - Patients', 'description': 'Staff-only patient directory and account activation management.'},
        {'name': 'Admin - Doctors', 'description': 'Staff-only clinic doctor directory management.'},
        {'name': 'Admin - Schedules', 'description': 'Staff-only recurring doctor schedule management.'},
        {'name': 'Admin - Appointments', 'description': 'Staff-only appointment review and cancellation.'},
    ],
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
}
