from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from rest_framework import generics, permissions, serializers
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view

from appointments.models import Appointment
from doctors.models import Doctor, WeeklySchedule
from doctors.serializers import DoctorSerializer
from doctors.serializers import AdminScheduleSerializer


class AvailabilitySlotSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField()
    status = serializers.ChoiceField(choices=["available", "booked", "unavailable"])


@extend_schema(tags=["Patient - Doctors"])
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def doctor_list(request):
    doctors = Doctor.objects.filter(active=True).prefetch_related("weekly_schedules").all()
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)


@extend_schema(tags=["Patient - Doctors"])
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def doctor_detail(request, doctor_id):
    try:
        doctor = Doctor.objects.filter(active=True).prefetch_related("weekly_schedules").get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

    serializer = DoctorSerializer(doctor)
    return Response(serializer.data)


@extend_schema(
    tags=["Patient - Slots"],
    parameters=[
        OpenApiParameter("doctor_id", OpenApiTypes.INT, OpenApiParameter.PATH),
        OpenApiParameter(
            "date",
            OpenApiTypes.DATE,
            OpenApiParameter.QUERY,
            required=True,
            description="Date to check in the clinic timezone (Africa/Nairobi), formatted as YYYY-MM-DD.",
        ),
    ],
    responses=AvailabilitySlotSerializer(many=True),
)
@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def doctor_availability(request, doctor_id):
    try:
        doctor = Doctor.objects.get(pk=doctor_id)
    except Doctor.DoesNotExist:
        return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)

    if not doctor.active:
        return Response({"detail": "Doctor is inactive."}, status=status.HTTP_404_NOT_FOUND)

    requested_date = request.query_params.get("date")
    if not requested_date:
        return Response({"detail": "Date query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        clinic_date = date.fromisoformat(requested_date)
    except ValueError:
        return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

    tz = ZoneInfo("Africa/Nairobi")
    slots = []
    for schedule in WeeklySchedule.objects.filter(doctor=doctor, weekday=clinic_date.weekday()).order_by("start_time"):
        current = datetime.combine(clinic_date, schedule.start_time, tzinfo=tz)
        end = datetime.combine(clinic_date, schedule.end_time, tzinfo=tz)
        while current + timedelta(minutes=30) <= end:
            slots.append(current)
            current += timedelta(minutes=30)
    slots = sorted(set(slots))

    day_start = datetime.combine(clinic_date, time.min, tzinfo=tz)
    day_end = day_start + timedelta(days=1)
    appointments = Appointment.objects.filter(
        doctor=doctor,
        status=Appointment.STATUS_BOOKED,
        start_at__lt=day_end.astimezone(UTC),
        end_at__gt=day_start.astimezone(UTC),
    )
    booked_appointments = list(appointments)
    patient_appointments = []
    if request.user.is_authenticated:
        patient_appointments = list(
            Appointment.objects.filter(
                patient=request.user,
                status=Appointment.STATUS_BOOKED,
                start_at__lt=day_end.astimezone(UTC),
                end_at__gt=day_start.astimezone(UTC),
            )
        )

    now = timezone.now().astimezone(tz)
    results = []
    for slot_start in slots:
        slot_end = slot_start + timedelta(minutes=30)
        is_booked = any(
            appointment.start_at < slot_end.astimezone(UTC)
            and appointment.end_at > slot_start.astimezone(UTC)
            for appointment in booked_appointments
        )
        if is_booked:
            slot_status = "booked"
        elif slot_start < now + timedelta(hours=1):
            slot_status = "unavailable"
        else:
            slot_status = "available"
        if slot_status == "available" and any(
            appointment.start_at < slot_end.astimezone(UTC)
            and appointment.end_at > slot_start.astimezone(UTC)
            for appointment in patient_appointments
        ):
            slot_status = "unavailable"
        results.append({"start_at": slot_start.isoformat(), "status": slot_status})

    return Response(results)


@extend_schema_view(
    get=extend_schema(tags=["Admin - Doctors"]),
    post=extend_schema(tags=["Admin - Doctors"]),
)
class AdminDoctorListView(generics.ListCreateAPIView):
    queryset = Doctor.objects.prefetch_related("weekly_schedules").all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]


@extend_schema_view(
    get=extend_schema(tags=["Admin - Doctors"]),
    put=extend_schema(tags=["Admin - Doctors"]),
    patch=extend_schema(tags=["Admin - Doctors"]),
)
class AdminDoctorDetailView(generics.RetrieveUpdateAPIView):
    queryset = Doctor.objects.prefetch_related("weekly_schedules").all()
    serializer_class = DoctorSerializer
    permission_classes = [permissions.IsAdminUser]


@extend_schema_view(
    get=extend_schema(tags=["Admin - Schedules"]),
    post=extend_schema(tags=["Admin - Schedules"]),
)
class AdminScheduleListView(generics.ListCreateAPIView):
    serializer_class = AdminScheduleSerializer
    permission_classes = [permissions.IsAdminUser]

    def get_queryset(self):
        queryset = WeeklySchedule.objects.select_related("doctor").all()
        doctor_id = self.request.query_params.get("doctor")
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        return queryset


@extend_schema_view(
    get=extend_schema(tags=["Admin - Schedules"]),
    put=extend_schema(tags=["Admin - Schedules"]),
    patch=extend_schema(tags=["Admin - Schedules"]),
    delete=extend_schema(tags=["Admin - Schedules"]),
)
class AdminScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WeeklySchedule.objects.select_related("doctor").all()
    serializer_class = AdminScheduleSerializer
    permission_classes = [permissions.IsAdminUser]
