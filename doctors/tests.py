from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from appointments.models import Appointment
from doctors.models import Doctor, WeeklySchedule


User = get_user_model()
CLINIC_TZ = ZoneInfo("Africa/Nairobi")


class DoctorAvailabilityTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.patient = User.objects.create_user(
            username="availability-patient",
            email="availability-patient@example.com",
            password="Patient-pass-123!",
        )
        self.doctor = Doctor.objects.create(name="Dr. Availability")
        self.clinic_date = timezone.localdate() + timedelta(days=7)
        WeeklySchedule.objects.create(
            doctor=self.doctor,
            weekday=self.clinic_date.weekday(),
            start_time=time(10, 0),
            end_time=time(11, 30),
        )
        self.booked_start = datetime.combine(
            self.clinic_date,
            time(10, 30),
            tzinfo=CLINIC_TZ,
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            start_at=self.booked_start,
            end_at=self.booked_start + timedelta(minutes=30),
        )

    def test_availability_lists_scheduled_slots_and_marks_booked_slots(self):
        response = self.client.get(
            f"/api/doctors/{self.doctor.id}/availability/",
            {"date": self.clinic_date.isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [slot["status"] for slot in response.data],
            ["available", "booked", "available"],
        )
        self.assertEqual(
            [datetime.fromisoformat(slot["start_at"]).time() for slot in response.data],
            [time(10, 0), time(10, 30), time(11, 0)],
        )
        self.assertNotIn("patient", response.data[1])

    def test_cancelling_appointment_releases_slot_as_available(self):
        self.appointment.status = Appointment.STATUS_CANCELLED
        self.appointment.save(update_fields=["status"])

        response = self.client.get(
            f"/api/doctors/{self.doctor.id}/availability/",
            {"date": self.clinic_date.isoformat()},
        )

        self.assertEqual(
            [slot["status"] for slot in response.data],
            ["available", "available", "available"],
        )

    def test_no_schedule_returns_no_slots(self):
        response = self.client.get(
            f"/api/doctors/{self.doctor.id}/availability/",
            {"date": (self.clinic_date + timedelta(days=1)).isoformat()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_month_availability_returns_daily_slots_and_personal_conflicts(self):
        self.client.force_authenticate(self.patient)
        response = self.client.get(
            f"/api/doctors/{self.doctor.id}/availability/month/",
            {"month": self.clinic_date.strftime("%Y-%m")},
        )

        self.assertEqual(response.status_code, 200)
        day = next(
            item for item in response.data
            if item["date"] == self.clinic_date.isoformat()
        )
        self.assertEqual(
            [slot["status"] for slot in day["slots"]],
            ["available", "booked", "available"],
        )
        month_start = date(self.clinic_date.year, self.clinic_date.month, 1)
        if month_start.month == 12:
            next_month = date(month_start.year + 1, 1, 1)
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)
        self.assertEqual(len(response.data), (next_month - month_start).days)

    def test_month_availability_rejects_invalid_month(self):
        response = self.client.get(
            f"/api/doctors/{self.doctor.id}/availability/month/",
            {"month": "2026-13"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["detail"], "Invalid month format. Use YYYY-MM.")

    def test_staff_can_manage_doctors_and_schedules(self):
        admin = User.objects.create_superuser(
            username="doctor-admin",
            email="doctor-admin@example.com",
            password="Admin-pass-123!",
        )
        self.client.force_authenticate(admin)

        created = self.client.post(
            "/api/doctors/admin/doctors/",
            {"name": "Dr. New", "specialty": "Family medicine", "active": True},
        )
        self.assertEqual(created.status_code, 201)
        new_doctor_id = created.data["id"]

        schedule = self.client.post(
            "/api/doctors/admin/schedules/",
            {
                "doctor": new_doctor_id,
                "weekday": 2,
                "start_time": "09:00:00",
                "end_time": "12:00:00",
            },
        )
        self.assertEqual(schedule.status_code, 201)
        self.assertEqual(schedule.data["doctor"], new_doctor_id)

        invalid_schedule = self.client.post(
            "/api/doctors/admin/schedules/",
            {
                "doctor": new_doctor_id,
                "weekday": 2,
                "start_time": "09:15:00",
                "end_time": "12:00:00",
            },
        )
        self.assertEqual(invalid_schedule.status_code, 400)

        updated = self.client.patch(
            f"/api/doctors/admin/doctors/{new_doctor_id}/",
            {"active": False},
        )
        self.assertEqual(updated.status_code, 200)
        self.assertFalse(updated.data["active"])
