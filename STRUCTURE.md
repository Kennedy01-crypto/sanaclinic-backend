# Sanaclinic Backend structure

This system backend is designed as a Django project with three domain apps.

```text
backend/
├── manage.py
├── requirements.txt
├── pytest.ini
├── README.md                   # General system readme markdown file
├── AI_REFLECTION.md            # My Ai usage reflection
├── STRUCTURE.md                # System Design
├── .env                        # Local secrets and PostgreSQL connection URL (never commit)
├── clinic_backend/
│   ├── __init__.py
│   ├── settings.py             # Django, REST framework, database, timezone, CORS/JWT settings
│   ├── urls.py                 # Admin, API, and schema routes
│   ├── authentication.py       # JWT authentication from the access-token cookie
│   ├── asgi.py                 # ASGI application entry point
│   └── wsgi.py                 # WSGI application entry point
├── accounts/
│   ├── models.py               # Custom patient user model
│   ├── serializers.py          # Registration, profile, password, role, and patient management serializers
│   ├── views.py                # Auth/profile plus staff-only dashboard and patient management APIs
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
├── doctors/
│   ├── models.py               # Doctor and weekly working-period models
│   ├── serializers.py
│   ├── views.py                # Public doctor availability and staff-only doctor/schedule management
│   ├── urls.py
│   ├── admin.py
│   ├── tests.py
│   └── migrations/
└── appointments/
    ├── models.py               # Appointment lifecycle and patient/doctor relationships
    ├── serializers.py
    ├── views.py                # Booking/history and staff-only appointment management endpoints
    ├── urls.py
    ├── admin.py
    ├── tests.py
    └── migrations/
```

## Framework and responsibilities

- **Django 5.2** provides the application framework, ORM, migrations, and admin.
- **Django REST Framework** exposes JSON API endpoints and enforces authentication and permissions.
- **Simple JWT** provides access/refresh tokens; the configured authentication class can read the access token from an HttpOnly cookie.
- **drf-spectacular** generates the OpenAPI schema and Swagger UI.
- **PostgreSQL** is required and configured by parsing `DATABASE_URL`; `psycopg` is pinned in requirements. SQLite fallback is disabled.

Each app owns its domain models, serializers, URLs, admin integration, and tests. The current appointment validation is implemented in the appointment views; a dedicated service module has not yet been added.

The account role returned by `/api/accounts/me/` is derived from Django's existing `is_staff` flag (`admin` for staff, otherwise `patient`). Public registration and profile serializers do not accept role or staff fields. The admin summary endpoint enforces DRF's `IsAdminUser` permission.

## Useful commands

From `backend/`:

```powershell
python manage.py check
python manage.py makemigrations
python manage.py migrate
python manage.py test
```

See [README.md](./README.md) for route details.