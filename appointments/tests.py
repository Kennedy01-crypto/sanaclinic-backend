from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from doctors.models import Doctor, WeeklySchedule


User = get_user_model()
CLINIC_TZ = ZoneInfo("Africa/Nairobi")


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


class PatientAppointmentWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username="booking-patient",
            email="booking-patient@example.com",
            password="Patient-pass-123!",
        )
        self.other_patient = User.objects.create_user(
            username="other-booking-patient",
            email="other-booking-patient@example.com",
            password="Patient-pass-123!",
        )
        self.doctor = Doctor.objects.create(name="Dr. Booking")
        self.other_doctor = Doctor.objects.create(name="Dr. Other Booking")
        self.booking_date = timezone.localdate() + timedelta(days=7)
        for doctor in (self.doctor, self.other_doctor):
            WeeklySchedule.objects.create(
                doctor=doctor,
                weekday=self.booking_date.weekday(),
                start_time=time(9, 0),
                end_time=time(12, 0),
            )
        self.first_slot = datetime.combine(
            self.booking_date, time(10, 0), tzinfo=CLINIC_TZ
        )
        self.second_slot = datetime.combine(
            self.booking_date, time(10, 30), tzinfo=CLINIC_TZ
        )
        self.third_slot = datetime.combine(
            self.booking_date, time(11, 0), tzinfo=CLINIC_TZ
        )
        self.client.force_authenticate(self.patient)

    def _book(self, start_at, doctor=None):
        return self.client.post(
            "/api/appointments/",
            {
                "doctor_id": (doctor or self.doctor).id,
                "start_at": start_at.isoformat(),
            },
            format="json",
        )

    def test_patient_can_book_a_scheduled_future_slot(self):
        response = self._book(self.first_slot)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["status"], Appointment.STATUS_BOOKED)
        self.assertEqual(response.data["doctor"], self.doctor.id)
        self.assertEqual(response.data["patient"], self.patient.id)

    def test_booking_an_occupied_doctor_slot_returns_conflict(self):
        self.assertEqual(self._book(self.first_slot).status_code, 201)
        self.client.force_authenticate(self.other_patient)

        response = self._book(self.first_slot)

        self.assertEqual(response.status_code, 409)

    def test_patient_cannot_book_overlapping_appointments_with_different_doctors(self):
        self.assertEqual(self._book(self.first_slot).status_code, 201)

        response = self._book(self.first_slot, doctor=self.other_doctor)

        self.assertEqual(response.status_code, 409)

    def test_patient_can_cancel_and_book_the_released_slot_again(self):
        booking = self._book(self.first_slot)
        appointment_id = booking.data["id"]

        cancelled = self.client.patch(
            f"/api/appointments/{appointment_id}/cancel/",
            {"reason": "Schedule changed"},
            format="json",
        )
        self.assertEqual(cancelled.status_code, 200)
        self.assertEqual(
            self.client.patch(
                f"/api/appointments/{appointment_id}/cancel/",
                {"reason": "Repeated request"},
                format="json",
            ).status_code,
            409,
        )
        self.assertEqual(self._book(self.first_slot).status_code, 201)

    def test_patient_can_reschedule_and_release_the_original_slot(self):
        booking = self._book(self.first_slot)
        appointment_id = booking.data["id"]

        response = self.client.patch(
            f"/api/appointments/{appointment_id}/reschedule/",
            {"start_at": self.second_slot.isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        appointment = Appointment.objects.get(pk=appointment_id)
        self.assertEqual(appointment.start_at, self.second_slot)
        self.client.force_authenticate(self.other_patient)
        self.assertEqual(self._book(self.first_slot).status_code, 201)

    def test_rescheduling_to_an_occupied_slot_returns_conflict_without_moving(self):
        original = self._book(self.first_slot)
        self.client.force_authenticate(self.other_patient)
        self.assertEqual(self._book(self.second_slot).status_code, 201)
        self.client.force_authenticate(self.patient)

        response = self.client.patch(
            f"/api/appointments/{original.data['id']}/reschedule/",
            {"start_at": self.second_slot.isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, 409)
        appointment = Appointment.objects.get(pk=original.data["id"])
        self.assertEqual(appointment.start_at, self.first_slot)

    def test_cancelled_appointment_cannot_be_rescheduled(self):
        booking = self._book(self.first_slot)
        appointment_id = booking.data["id"]
        self.client.patch(
            f"/api/appointments/{appointment_id}/cancel/",
            {"reason": "No longer needed"},
            format="json",
        )

        response = self.client.patch(
            f"/api/appointments/{appointment_id}/reschedule/",
            {"start_at": self.second_slot.isoformat()},
            format="json",
        )

        self.assertEqual(response.status_code, 409)

    def test_patient_history_contains_only_upcoming_booked_appointments(self):
        now = timezone.now()
        past_start = now - timedelta(days=2)
        future_start = now + timedelta(days=2)
        cancelled_start = now + timedelta(days=3)
        later_future_start = now + timedelta(days=4)
        past = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=past_start,
            end_at=past_start + timedelta(minutes=30),
        )
        upcoming = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=future_start,
            end_at=future_start + timedelta(minutes=30),
        )
        cancelled = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=cancelled_start,
            end_at=cancelled_start + timedelta(minutes=30),
            status=Appointment.STATUS_CANCELLED,
        )
        later_upcoming = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=later_future_start,
            end_at=later_future_start + timedelta(minutes=30),
        )

        response = self.client.get(
            f"/api/appointments/patients/{self.patient.id}/appointments/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [item["id"] for item in response.data],
            [upcoming.id, later_upcoming.id],
        )
        result_ids = [item["id"] for item in response.data]
        self.assertNotIn(past.id, result_ids)
        self.assertNotIn(cancelled.id, result_ids)


class AppointmentExclusionConstraintTests(TestCase):
    def setUp(self):
        self.patient = User.objects.create_user(
            username="constraint-patient",
            email="constraint-patient@example.com",
            password="Patient-pass-123!",
        )
        self.other_patient = User.objects.create_user(
            username="constraint-other-patient",
            email="constraint-other-patient@example.com",
            password="Patient-pass-123!",
        )
        self.doctor = Doctor.objects.create(name="Dr. Constraint")
        self.other_doctor = Doctor.objects.create(name="Dr. Other Constraint")
        self.start_at = timezone.now() + timedelta(days=5)

    def test_database_rejects_overlapping_bookings_for_the_same_doctor(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=self.start_at,
            end_at=self.start_at + timedelta(minutes=30),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    patient=self.other_patient,
                    doctor=self.doctor,
                    start_at=self.start_at,
                    end_at=self.start_at + timedelta(minutes=30),
                )

    def test_database_rejects_overlapping_bookings_for_the_same_patient(self):
        Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=self.start_at,
            end_at=self.start_at + timedelta(minutes=30),
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    patient=self.patient,
                    doctor=self.other_doctor,
                    start_at=self.start_at,
                    end_at=self.start_at + timedelta(minutes=30),
                )
