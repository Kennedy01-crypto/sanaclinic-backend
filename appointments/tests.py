from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from doctors.models import Doctor


User = get_user_model()


class AdminAppointmentManagementTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            username="appointment-admin",
            email="appointment-admin@example.com",
            password="Admin-pass-123!",
        )
        self.patient = User.objects.create_user(
            username="appointment-patient",
            email="appointment-patient@example.com",
            password="Patient-pass-123!",
        )
        self.doctor = Doctor.objects.create(name="Dr. Appointment")
        start_at = timezone.now() + timedelta(days=3)
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=start_at,
            end_at=start_at + timedelta(minutes=30),
        )

    def test_admin_can_list_and_cancel_appointment(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get("/api/appointments/admin/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["patient_name"], "appointment-patient")
        self.assertEqual(response.data[0]["doctor_name"], "Dr. Appointment")

        cancelled = self.client.post(
            f"/api/appointments/admin/{self.appointment.id}/cancel/",
            {"reason": "Clinic schedule change"},
        )
        self.assertEqual(cancelled.status_code, 200)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, Appointment.STATUS_CANCELLED)

    def test_non_staff_cannot_manage_appointments(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get("/api/appointments/admin/")
        self.assertEqual(response.status_code, 403)
