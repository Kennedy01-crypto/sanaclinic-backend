# Clinic Booking Backend System

The backend is a Django REST Framework API for patient accounts, doctors, weekly schedules, and appointments. It uses PostgreSQL and serves JSON endpoints under `/api/`.

## SECTION 1: System Design

`NOTE:` Find more detailed System design Documentation in [STRUCTURE.md](./STRUCTURE.md)

The backend is organized as a Django project with three domain apps. Each app owns its models, serializers, routes, and API views. Django REST Framework handles API requests, authentication, and permissions; PostgreSQL stores application data.

```text
Client
  └── Django REST Framework API
       ├── accounts      — patient accounts, authentication, staff patient management
       ├── doctors       — doctor directory, recurring weekly schedules, availability
       └── appointments  — booking, cancellation, rescheduling, appointment history
              └── PostgreSQL
```

Authentication uses Simple JWT. The API supports HttpOnly cookie authentication for the frontend and a token endpoint for bearer-token clients such as Swagger UI. Staff-only management endpoints use Django's staff permission. The clinic timezone is `Africa/Nairobi`.

## Models & Components

### Data models

- **User** (`accounts`): extends Django's `AbstractUser`; adds unique email, phone, date of birth, and emergency contact fields. Staff status determines whether the API treats the account as an administrator.
- **Doctor** (`doctors`): stores a doctor's name, specialty, active status, and timestamps. Doctors are records, not user login accounts.
- **WeeklySchedule** (`doctors`): stores a doctor's recurring weekday working period. Periods must have a start before the end and align to 30-minute slots.
- **Appointment** (`appointments`): links a patient and doctor to a start and end time. Its status is booked or cancelled; cancellation reason and timestamp are retained. Database indexes support common doctor- and patient-time queries.

### Application components

- **`accounts`**: registration, login/token refresh/logout, profile and password operations, plus staff dashboard and patient management APIs.
- **`doctors`**: public doctor listing and availability, plus staff doctor and schedule management APIs.
- **`appointments`**: patient booking, cancellation, rescheduling, and appointment history, plus staff appointment management.
- **`clinic_backend`**: Django settings, URL configuration, cookie JWT authentication, and ASGI/WSGI entry points.
- **Django REST Framework**: JSON API, authentication and permissions, and request throttling.
- **Simple JWT**: access and refresh tokens.
- **drf-spectacular**: OpenAPI schema and Swagger UI.
- **PostgreSQL**: required relational database, configured with `DATABASE_URL`.

See [STRUCTURE.md](./STRUCTURE.md) for the backend directory layout.

## Key Decisions Made

- Use a custom user model from the start so patient-specific fields are part of the project's authentication model.
- Use Django's existing `is_staff` flag to distinguish administrators from patients, and protect administrative APIs with staff permissions.
- Represent doctors separately from login accounts because the current system does not provide doctor sign-in.
- Store recurring weekly work periods and expose availability as configured 30-minute appointment slots.
- Keep cancelled appointments as records with cancellation details instead of deleting booking history.
- Require PostgreSQL through `DATABASE_URL`; SQLite fallback is disabled so local commands cannot silently use a different database.
- Use JWTs in HttpOnly cookies for the frontend while retaining a bearer-token endpoint for API tools.
- Generate the API schema and Swagger UI from the API definitions with `drf-spectacular`.

## Trade-offs Considered

- **A simpler built-in user model vs. a custom user model:** the custom model adds setup and migration responsibility, but avoids retrofitting patient fields and identity later.
- **One staff flag vs. a separate role/permission model:** `is_staff` is simple for the current patient/admin roles, but it is less expressive if additional roles are introduced.
- **Doctors as records vs. doctor accounts:** records keep the current scope focused on patient booking and staff management, but do not support doctor self-service.
- **Recurring weekly schedules vs. date-specific availability:** weekly schedules are straightforward to manage, but do not represent holidays, exceptions, or one-off schedule changes.
- **Fixed 30-minute slots vs. configurable appointment lengths:** fixed slots make availability and booking predictable, but constrain appointment duration and schedule granularity.
- **PostgreSQL-only configuration vs. an SQLite development fallback:** requiring the production database engine locally reduces environment differences, but means local development and tests need PostgreSQL configuration.
- **Retaining cancelled records vs. deleting them:** preserving history supports traceability, while requiring status-aware logic wherever availability or appointment lists are calculated.

## Public URL of Deployed Application

- **Backend API:** https://sanaclinic-backend.vercel.app/
- **Swagger UI:** https://sanaclinic-backend.vercel.app/api/docs/
- **OpenAPI schema:** https://sanaclinic-backend.vercel.app/api/schema/
- **Django Admin:** https://sanaclinic-backend.vercel.app/admin/



## Local Development

Configure a PostgreSQL connection in `backend/.env` using `DATABASE_URL`. The settings also read `DJANGO_SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, and `CSRF_TRUSTED_ORIGINS`. For local development set `DEBUG=True`; when `DEBUG=False`, `DJANGO_SECRET_KEY` must be explicitly configured. Do not commit secrets or use development settings in a public deployment.

From this directory, create and activate a virtual environment, install dependencies, apply migrations, and start Django:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Run the backend checks and tests with the same PostgreSQL configuration:

```powershell
python manage.py check
python manage.py test
```

## SECTION 2: API Routes

Routes are mounted under `/api/` and use trailing slashes:

## Accounts

- `/api/accounts/register/`, `/api/accounts/login/`, `/api/accounts/refresh/`, `/api/accounts/logout/`
- `/api/accounts/token/` (JWT pair for Swagger/API bearer authorization)
- `/api/accounts/me/`, `/api/accounts/profile/`, `/api/accounts/change-password/`
- `/api/accounts/admin/summary/` (staff only)
- `/api/accounts/admin/patients/` and `/api/accounts/admin/patients/{id}/` (staff only)

## Doctors
- `/api/doctors/`, `/api/doctors/{id}/`, `/api/doctors/{id}/availability/`
- `/api/doctors/admin/doctors/`, `/api/doctors/admin/doctors/{id}/` (staff only)
- `/api/doctors/admin/schedules/`, `/api/doctors/admin/schedules/{id}/` (staff only)

## Apointments
- `/api/appointments/admin/` and `/api/appointments/admin/{id}/cancel/` (staff only)
- `/api/appointments/`, `/api/appointments/{id}/cancel/`, `/api/appointments/{id}/reschedule/`
- `/api/appointments/patients/{id}/appointments/`

## Documentation
- `/api/docs/` (Swagger UI) and `/api/schema/` (OpenAPI schema)
- `/admin/` (Django administrator interface)

The availability endpoint returns configured 30-minute slots with a start time and `available`, `booked`, or `unavailable` status. Booked slots do not expose patient details. Booking is validated by the API. Swagger UI supports bearer authorization; the normal login endpoint continues to use HttpOnly cookies for the frontend.

## SECTION 3: DEPLOYMENT & CI/CD


The GitHub Actions workflow is [`.github/workflows/ci-cd.yml`](./.github/workflows/ci-cd.yml).

**1. Branch and deployment:** 

GitHub Actions runs backend checks on pull requests targeting `main` and on pushes to `main`. Vercel's Git integration deploys production from `main` after changes are pushed or merged. GitHub Actions only validates the code; it does not deploy.

**2. CI/CD Pipeline:** 

Actions starts a PostgreSQL service, installs the pinned Python dependencies, runs `manage.py check`, and runs the Django test suite. No Vercel credentials or deployment secrets are needed in GitHub Actions.

Protect the `main` branch and require the `test` status check before allowing pull requests to merge. This makes successful checks a merge requirement; direct pushes to `main` should be disallowed if every production change must pass the checks.

`3.Production environment variables`

These are configured in the Vercel project settings. 
Required settings include 

`DJANGO_SECRET_KEY`, 

`DEBUG=False`, 

`ALLOWED_HOSTS`, 

`CORS_ALLOWED_ORIGINS`, 

`CSRF_TRUSTED_ORIGINS`, and PostgreSQL `DATABASE_URL`. 

The default `ALLOWED_HOSTS` includes `.vercel.app`, `localhost`, and `127.0.0.1`; an explicit environment value overrides it. The `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` settings allow `https://sanaclinic-frontend.vercel.app` and normalize trailing slashes. Environment values can add other origins; the production frontend origin remains allowed.

The decoupled frontend uses

`NEXT_PUBLIC_API_URL=https://sanaclinic-backend.vercel.app/api` and 

`NEXT_PUBLIC_DJANGO_URL=https://sanaclinic-backend.vercel.app`

## SECTION 4: AI REFLECTION
See [AI_REFLECTION.md](./AI_REFLECTION.md) for the my AI usage reflection.