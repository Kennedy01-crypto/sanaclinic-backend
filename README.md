# Backend

The backend is a Django REST Framework API for patient accounts, doctors, weekly schedules, and appointments.

## Tech stack

- Python
- Django 5.2
- Django REST Framework
- Simple JWT for JWT authentication
- `django-cors-headers` for cross-origin configuration
- `drf-spectacular` for OpenAPI schema and Swagger UI
- PostgreSQL via `DATABASE_URL` (required)

Pinned Python dependencies are listed in [requirements.txt](./requirements.txt). The project timezone is `Africa/Nairobi`.

## Applications

- `accounts`: custom user model, serializers, patient auth/profile endpoints, staff-only dashboard summary, and patient management endpoints.
- `doctors`: doctor and recurring weekly schedule models, serializers, public availability, and staff-only doctor/schedule management endpoints.
- `appointments`: appointment model, booking, cancellation, rescheduling, patient history, and staff appointment management endpoints.
- `clinic_backend`: Django project settings, URL configuration, ASGI/WSGI entry points, and cookie JWT authentication.

See [STRUCTURE.md](./STRUCTURE.md) for the directory tree.

## Run

Configure `backend/.env` with a PostgreSQL `DATABASE_URL` first. SQLite fallback is disabled so management commands cannot silently create a local database.

From this directory, create/activate a virtual environment, install dependencies, apply migrations, and start Django:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

The full repository instructions are in [../RUN.md](../RUN.md).

## Local API routes

Routes are currently mounted under `/api/` and use trailing slashes:

- `/api/accounts/register/`, `/api/accounts/login/`, `/api/accounts/refresh/`, `/api/accounts/logout/`
- `/api/accounts/token/` (JWT pair for Swagger/API bearer authorization)
- `/api/accounts/me/`, `/api/accounts/profile/`, `/api/accounts/change-password/`
- `/api/accounts/admin/summary/` (staff only; role comes from Django `is_staff`)
- `/api/accounts/admin/patients/` and `/api/accounts/admin/patients/{id}/` (staff only)
- `/api/doctors/`, `/api/doctors/{id}/`, `/api/doctors/{id}/availability/`
- `/api/doctors/admin/doctors/`, `/api/doctors/admin/doctors/{id}/` (staff only)
- `/api/doctors/admin/schedules/`, `/api/doctors/admin/schedules/{id}/` (staff only)
- `/api/appointments/admin/` and `/api/appointments/admin/{id}/cancel/` (staff only)
- `/api/appointments/`, `/api/appointments/{id}/cancel/`, `/api/appointments/{id}/reschedule/`
- `/api/appointments/patients/{id}/appointments/`
- `/api/docs/` and `/api/schema/`
- `/admin/` for Django's built-in administrator interface.

The doctor availability endpoint returns only configured 30-minute schedule slots, each with a `start_at` and a status of `available`, `booked`, or `unavailable`. Booked slots include no patient details; cancelled appointments release their slots. Booking is independently validated by the API.

Swagger UI at `/api/docs/` supports JWT bearer authorization and persists the authorized token in browser storage. Use `/api/accounts/token/` with a username and password to obtain an access token, then click **Authorize** and provide the token. The normal `/api/accounts/login/` endpoint continues to use HttpOnly cookies for the frontend.

Swagger groups API operations into Patient categories (Accounts, Doctors, Slots, and Appointments) followed by Admin categories (Dashboard, Patients, Doctors, Schedules, and Appointments). Admin operations require a staff account; patient appointment operations require authentication and apply to the signed-in patient.

This is a description of current routes, not a guarantee that all assessment requirements or concurrency protections are complete.
