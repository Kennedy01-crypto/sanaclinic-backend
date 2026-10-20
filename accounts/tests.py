from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


User = get_user_model()


class RoleBasedAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username="patient",
            email="patient@example.com",
            password="Patient-pass-123!",
        )
        self.admin = User.objects.create_superuser(
            username="clinic-admin",
            email="admin@example.com",
            password="Admin-pass-123!",
        )

    def test_current_user_role_is_derived_from_staff_flag(self):
        self.client.force_authenticate(self.patient)
        patient_response = self.client.get("/api/accounts/me/")
        self.assertEqual(patient_response.status_code, 200)
        self.assertEqual(patient_response.data["role"], "patient")

        staff_user = User.objects.create_user(
            username="staff-admin",
            email="staff-admin@example.com",
            password="Staff-pass-123!",
            is_staff=True,
        )
        self.client.force_authenticate(staff_user)
        admin_response = self.client.get("/api/accounts/me/")
        self.assertEqual(admin_response.status_code, 200)
        self.assertEqual(admin_response.data["role"], "admin")

    def test_registration_cannot_assign_privileged_fields(self):
        response = self.client.post(
            "/api/accounts/register/",
            {
                "username": "new-patient",
                "email": "new-patient@example.com",
                "password": "A-strong-password-123!",
                "is_staff": True,
                "is_superuser": True,
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 201)
        created_user = User.objects.get(username="new-patient")
        self.assertFalse(created_user.is_staff)
        self.assertFalse(created_user.is_superuser)

    def test_profile_update_cannot_change_role(self):
        self.client.force_authenticate(self.patient)
        response = self.client.patch(
            "/api/accounts/profile/",
            {"is_staff": True, "role": "admin"},
        )
        self.assertEqual(response.status_code, 200)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_staff)
        self.client.force_authenticate(self.patient)
        current_user = self.client.get("/api/accounts/me/")
        self.assertEqual(current_user.data["role"], "patient")

    def test_admin_summary_requires_staff_user(self):
        response = self.client.get("/api/accounts/admin/summary/")
        self.assertEqual(response.status_code, 401)

        self.client.force_authenticate(self.patient)
        response = self.client.get("/api/accounts/admin/summary/")
        self.assertEqual(response.status_code, 403)

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/accounts/admin/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["patients"], 1)

    def test_bearer_token_from_token_endpoint_authorizes_protected_api(self):
        token_response = self.client.post(
            "/api/accounts/token/",
            {"username": "clinic-admin", "password": "Admin-pass-123!"},
        )
        self.assertEqual(token_response.status_code, 200)
        self.assertIn("access", token_response.data)

        response = self.client.get(
            "/api/accounts/admin/summary/",
            HTTP_AUTHORIZATION=f"Bearer {token_response.data['access']}",
        )
        self.assertEqual(response.status_code, 200)

    def test_openapi_documents_bearer_authorization(self):
        response = self.client.get("/api/schema/")
        self.assertEqual(response.status_code, 200)
        paths = response.data["paths"]
        self.assertEqual(
            response.data["components"]["securitySchemes"]["BearerAuth"],
            {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
        )
        self.assertEqual(
            paths["/api/accounts/admin/summary/"]["get"]["security"],
            [{"BearerAuth": []}],
        )
        self.assertEqual(
            paths["/api/doctors/"]["get"].get("security", []),
            [{}],
        )
        expected_tags = {
            "/api/accounts/register/": "Patient - Accounts",
            "/api/accounts/admin/summary/": "Admin - Dashboard",
            "/api/accounts/admin/patients/": "Admin - Patients",
            "/api/doctors/": "Patient - Doctors",
            "/api/doctors/{doctor_id}/availability/": "Patient - Slots",
            "/api/doctors/admin/doctors/": "Admin - Doctors",
            "/api/doctors/admin/schedules/": "Admin - Schedules",
            "/api/appointments/": "Patient - Appointments",
            "/api/appointments/admin/": "Admin - Appointments",
        }
        for path, tag in expected_tags.items():
            method = "post" if path in {
                "/api/accounts/register/",
                "/api/appointments/",
            } else "get"
            self.assertEqual(paths[path][method]["tags"], [tag], path)
        schemas = response.data["components"]["schemas"]
        availability = paths["/api/doctors/{doctor_id}/availability/"]["get"]
        self.assertEqual(
            next(parameter for parameter in availability["parameters"] if parameter["name"] == "date")[
                "schema"
            ]["format"],
            "date",
        )
        self.assertTrue(
            next(parameter for parameter in availability["parameters"] if parameter["name"] == "date")[
                "required"
            ]
        )
        slot_response_schema = availability["responses"]["200"]["content"]["application/json"]["schema"]
        slot_schema_name = slot_response_schema["items"]["$ref"].rsplit("/", 1)[-1]
        self.assertEqual(
            set(schemas[slot_schema_name]["properties"]),
            {"start_at", "status"},
        )
        status_schema = schemas[slot_schema_name]["properties"]["status"]
        if "$ref" in status_schema:
            status_schema = schemas[status_schema["$ref"].rsplit("/", 1)[-1]]
        self.assertEqual(status_schema["enum"], ["available", "booked", "unavailable"])
        booking_schema = paths["/api/appointments/"]["post"]["requestBody"]["content"][
            "application/json"
        ]["schema"]
        self.assertEqual(
            set(schemas[booking_schema["$ref"].rsplit("/", 1)[-1]]["properties"]),
            {"doctor_id", "start_at"},
        )
        cancel_schema = paths["/api/appointments/{appointment_id}/cancel/"]["patch"][
            "requestBody"
        ]["content"]["application/json"]["schema"]
        self.assertEqual(
            set(schemas[cancel_schema["$ref"].rsplit("/", 1)[-1]]["properties"]),
            {"reason"},
        )
        reschedule_schema = paths["/api/appointments/{appointment_id}/reschedule/"]["patch"][
            "requestBody"
        ]["content"]["application/json"]["schema"]
        self.assertEqual(
            set(schemas[reschedule_schema["$ref"].rsplit("/", 1)[-1]]["properties"]),
            {"start_at"},
        )
        for path, path_item in paths.items():
            for method, operation in path_item.items():
                if method in {"get", "post", "put", "patch", "delete"}:
                    self.assertTrue(
                        operation["tags"][0].startswith(("Patient - ", "Admin - ")),
                        f"{method.upper()} {path} has no audience category",
                    )
        self.assertEqual(
            [tag["name"] for tag in response.data["tags"]],
            [
                "Patient - Accounts",
                "Patient - Doctors",
                "Patient - Slots",
                "Patient - Appointments",
                "Admin - Dashboard",
                "Admin - Patients",
                "Admin - Doctors",
                "Admin - Schedules",
                "Admin - Appointments",
            ],
        )
        docs_response = self.client.get("/api/docs/")
        self.assertEqual(docs_response.status_code, 200)
        self.assertIn(b'"persistAuthorization": true', docs_response.content)

    def test_admin_patient_management_is_staff_only_and_cannot_change_roles(self):
        self.client.force_authenticate(self.patient)
        denied = self.client.get("/api/accounts/admin/patients/")
        self.assertEqual(denied.status_code, 403)

        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/accounts/admin/patients/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["username"] for item in response.data], ["patient"])

        updated = self.client.patch(
            f"/api/accounts/admin/patients/{self.patient.id}/",
            {"is_active": False, "is_staff": True},
        )
        self.assertEqual(updated.status_code, 200)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)
        self.assertFalse(self.patient.is_staff)
