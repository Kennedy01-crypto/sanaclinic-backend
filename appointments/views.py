from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import transaction
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from appointments.models import Appointment
from appointments.serializers import (
    AdminAppointmentSerializer,
    AppointmentCancelRequestSerializer,
    AppointmentCreateRequestSerializer,
    AppointmentMessageSerializer,
    AppointmentRescheduleRequestSerializer,
    AppointmentRescheduleResponseSerializer,
    AppointmentSerializer,
)
from doctors.models import Doctor, WeeklySchedule


@extend_schema_view(get=extend_schema(tags=["Admin - Appointments"]))
class AdminAppointmentListView(generics.ListAPIView):
    serializer_class = AdminAppointmentSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = Appointment.objects.select_related("patient", "doctor").all()
        status_filter = self.request.query_params.get("status")
        if status_filter in {Appointment.STATUS_BOOKED, Appointment.STATUS_CANCELLED}:
            queryset = queryset.filter(status=status_filter)
        return queryset


@extend_schema_view(post=extend_schema(tags=["Admin - Appointments"]))
class AdminAppointmentCancelView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def post(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(pk=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        if appointment.status == Appointment.STATUS_CANCELLED:
            return Response({"detail": "This appointment has already been cancelled."}, status=status.HTTP_409_CONFLICT)
        if appointment.start_at <= timezone.now():
            return Response({"detail": "Only future appointments can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        reason = (request.data.get("reason") or "").strip()
        if not reason:
            return Response({"detail": "A cancellation reason is required."}, status=status.HTTP_400_BAD_REQUEST)

        appointment.status = Appointment.STATUS_CANCELLED
        appointment.cancellation_reason = reason
        appointment.cancelled_at = timezone.now()
        appointment.save(update_fields=["status", "cancellation_reason", "cancelled_at", "updated_at"])
        return Response(AdminAppointmentSerializer(appointment).data)

CLINIC_TZ = ZoneInfo("Africa/Nairobi")
SLOT_MINUTES = 30


def _validate_booking_request(doctor_id, start_at, patient, exclude_appointment_id=None):
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        raise ValueError("Doctor not found.")

    if not doctor.active:
        raise ValueError("Doctor is inactive.")

    if start_at.tzinfo is None:
        raise ValueError("Appointment start time must be timezone-aware.")

    start_local = start_at.astimezone(CLINIC_TZ)
    now_local = timezone.now().astimezone(CLINIC_TZ)
    if start_local < now_local:
        raise ValueError("Appointments cannot be in the past.")
    if start_local < now_local + timedelta(hours=1):
        raise ValueError("Appointments must be booked at least one hour in advance.")

    if start_local.minute not in (0, 30):
        raise ValueError("Appointments must start on a 30-minute boundary.")

    schedule_qs = WeeklySchedule.objects.filter(doctor=doctor, weekday=start_local.weekday())
    has_valid_period = False
    for schedule in schedule_qs:
        period_start = datetime.combine(start_local.date(), schedule.start_time, tzinfo=CLINIC_TZ)
        period_end = datetime.combine(start_local.date(), schedule.end_time, tzinfo=CLINIC_TZ)
        if period_start <= start_local and start_local + timedelta(minutes=30) <= period_end:
            has_valid_period = True
            break
    if not has_valid_period:
        raise ValueError("The requested slot does not fit inside a configured working period.")

    appointment_end = start_local + timedelta(minutes=30)
    overlapping_doctor = Appointment.objects.filter(
        doctor=doctor,
        status=Appointment.STATUS_BOOKED,
    ).filter(start_at__lt=appointment_end.astimezone(UTC), end_at__gt=start_local.astimezone(UTC))
    if exclude_appointment_id:
        overlapping_doctor = overlapping_doctor.exclude(pk=exclude_appointment_id)
    if overlapping_doctor.exists():
        raise ValueError("This doctor slot is already occupied.")

    overlapping_patient = Appointment.objects.filter(
        patient=patient,
        status=Appointment.STATUS_BOOKED,
    ).filter(start_at__lt=appointment_end.astimezone(UTC), end_at__gt=start_local.astimezone(UTC))
    if exclude_appointment_id:
        overlapping_patient = overlapping_patient.exclude(pk=exclude_appointment_id)
    if overlapping_patient.exists():
        raise ValueError("This patient already has an appointment at that time.")

    return doctor, start_local, appointment_end


@extend_schema(
    tags=["Patient - Appointments"],
    request=AppointmentCreateRequestSerializer,
    responses={201: AppointmentSerializer},
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_appointment(request):
    doctor_id = request.data.get("doctor_id")
    start_at = request.data.get("start_at")
    if not doctor_id or not start_at:
        return Response({"detail": "doctor_id and start_at are required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        start_dt = datetime.fromisoformat(start_at)
    except ValueError:
        return Response({"detail": "start_at must be an ISO 8601 datetime."}, status=status.HTTP_400_BAD_REQUEST)

    if start_dt.tzinfo is None:
        return Response({"detail": "Appointment start time must be timezone-aware."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        doctor, start_local, end_local = _validate_booking_request(doctor_id, start_dt, request.user)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    with transaction.atomic():
        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            start_at=start_local,
            end_at=end_local,
        )
    serializer = AppointmentSerializer(appointment)
    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([AllowAny])
def doctor_availability(request, doctor_id):
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

    if not doctor.active:
        return Response({"detail": "Doctor is inactive."}, status=status.HTTP_404_NOT_FOUND)

    date_value = request.query_params.get("date")
    if not date_value:
        return Response({"detail": "Date query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        clinic_date = date.fromisoformat(date_value)
    except ValueError:
        return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    slots = []
    for schedule in WeeklySchedule.objects.filter(doctor=doctor, weekday=clinic_date.weekday()).order_by("start_time"):
        current = datetime.combine(clinic_date, schedule.start_time, tzinfo=CLINIC_TZ)
        end = datetime.combine(clinic_date, schedule.end_time, tzinfo=CLINIC_TZ)
        while current + timedelta(minutes=30) <= end:
            slot_end = current + timedelta(minutes=30)
            slots.append(current)
            current = slot_end

    occupied = Appointment.objects.filter(
        doctor=doctor,
        status=Appointment.STATUS_BOOKED,
        start_at__date=clinic_date,
    )
    occupied_slots = set()
    for appt in occupied:
        start = appt.start_at.astimezone(CLINIC_TZ)
        end = appt.end_at.astimezone(CLINIC_TZ)
        while start < end:
            occupied_slots.add(start)
            start += timedelta(minutes=30)

    available = []
    for slot_start in slots:
        slot_end = slot_start + timedelta(minutes=30)
        if slot_start in occupied_slots:
            continue
        if slot_start < timezone.now().astimezone(CLINIC_TZ) + timedelta(hours=1):
            continue
        if request.user.is_authenticated:
            patient_conflicts = Appointment.objects.filter(
                patient=request.user,
                status=Appointment.STATUS_BOOKED,
            ).filter(start_at__lt=slot_end.astimezone(UTC), end_at__gt=slot_start.astimezone(UTC))
            if patient_conflicts.exists():
                continue
        available.append(slot_start.isoformat())

    return Response(available)


@extend_schema(
    tags=["Patient - Appointments"],
    parameters=[
        OpenApiParameter("appointment_id", OpenApiTypes.INT, OpenApiParameter.PATH),
    ],
    request=AppointmentCancelRequestSerializer,
    responses={200: AppointmentMessageSerializer},
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def cancel_appointment(request, appointment_id):
    reason = (request.data.get("reason") or "").strip()
    if not reason:
        return Response({"detail": "A cancellation reason is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        appointment = Appointment.objects.get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

    if appointment.patient_id != request.user.id:
        return Response({"detail": "You do not have permission to cancel this appointment."}, status=status.HTTP_403_FORBIDDEN)
    if appointment.status == Appointment.STATUS_CANCELLED:
        return Response({"detail": "This appointment has already been cancelled."}, status=status.HTTP_409_CONFLICT)
    if appointment.start_at <= timezone.now():
        return Response({"detail": "Only future appointments can be cancelled."}, status=status.HTTP_400_BAD_REQUEST)

    appointment.status = Appointment.STATUS_CANCELLED
    appointment.cancellation_reason = reason
    appointment.cancelled_at = timezone.now()
    appointment.save(update_fields=["status", "cancellation_reason", "cancelled_at", "updated_at"])
    return Response({"detail": "Appointment cancelled successfully."}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Patient - Appointments"],
    parameters=[
        OpenApiParameter("appointment_id", OpenApiTypes.INT, OpenApiParameter.PATH),
    ],
    request=AppointmentRescheduleRequestSerializer,
    responses={200: AppointmentRescheduleResponseSerializer},
)
@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def reschedule_appointment(request, appointment_id):
    start_at = request.data.get("start_at")
    if not start_at:
        return Response({"detail": "start_at is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        appointment = Appointment.objects.get(pk=appointment_id)
    except Appointment.DoesNotExist:
        return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

    if appointment.patient_id != request.user.id:
        return Response({"detail": "You do not have permission to reschedule this appointment."}, status=status.HTTP_403_FORBIDDEN)
    if appointment.status == Appointment.STATUS_CANCELLED:
        return Response({"detail": "Cancelled appointments cannot be rescheduled."}, status=status.HTTP_409_CONFLICT)
    if appointment.start_at <= timezone.now():
        return Response({"detail": "Only future appointments can be rescheduled."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        new_start = datetime.fromisoformat(start_at)
    except ValueError:
        return Response({"detail": "start_at must be an ISO 8601 datetime."}, status=status.HTTP_400_BAD_REQUEST)

    if new_start == appointment.start_at:
        return Response({"detail": "Rescheduling to the same time is not allowed."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        _, start_local, end_local = _validate_booking_request(appointment.doctor_id, new_start, request.user, exclude_appointment_id=appointment.id)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    original_start = appointment.start_at
    appointment.start_at = start_local
    appointment.end_at = end_local
    appointment.save(update_fields=["start_at", "end_at", "updated_at"])
    return Response({"detail": "Appointment rescheduled successfully.", "previous_start_at": original_start.isoformat(), "new_start_at": start_local.isoformat()}, status=status.HTTP_200_OK)


@extend_schema(
    tags=["Patient - Appointments"],
    parameters=[
        OpenApiParameter("patient_id", OpenApiTypes.INT, OpenApiParameter.PATH),
    ],
    responses={200: AppointmentSerializer(many=True)},
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def patient_appointments(request, patient_id):
    if int(patient_id) != int(request.user.id):
        return Response({"detail": "You are not allowed to view other patients' appointments."}, status=status.HTTP_403_FORBIDDEN)

    appointments = Appointment.objects.filter(patient_id=patient_id).order_by("start_at")
    serializer = AppointmentSerializer(appointments, many=True)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    return Response({"status": "ok", "timezone": "Africa/Nairobi"})
