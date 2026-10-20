from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from appointments.models import Appointment
from doctors.models import Doctor


class AppointmentCreateRequestSerializer(serializers.Serializer):
    doctor_id = serializers.IntegerField(help_text="ID of the doctor to book.")
    start_at = serializers.DateTimeField(
        help_text="Slot start time in ISO 8601 format, including a timezone offset."
    )


class AppointmentCancelRequestSerializer(serializers.Serializer):
    reason = serializers.CharField(help_text="Reason for cancelling the appointment.")


class AppointmentRescheduleRequestSerializer(serializers.Serializer):
    start_at = serializers.DateTimeField(
        help_text="New slot start time in ISO 8601 format, including a timezone offset."
    )


class AppointmentMessageSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AppointmentRescheduleResponseSerializer(serializers.Serializer):
    detail = serializers.CharField()
    previous_start_at = serializers.DateTimeField()
    new_start_at = serializers.DateTimeField()


class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(read_only=True)
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta:
        model = Appointment
        fields = [
            "id",
            "doctor",
            "patient",
            "start_at",
            "end_at",
            "status",
            "cancellation_reason",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["patient", "status", "cancelled_at", "created_at", "updated_at"]

    def validate(self, attrs):
        doctor = attrs.get("doctor")
        start_at = attrs.get("start_at")
        if not doctor or not start_at:
            return attrs

        if start_at.tzinfo is None or start_at < timezone.now():
            raise serializers.ValidationError({"start_at": "Appointment must be timezone-aware and in the future."})

        attrs["end_at"] = start_at + timedelta(minutes=30)
        return attrs


class AdminAppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.SerializerMethodField()
    doctor_name = serializers.CharField(source="doctor.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id",
            "patient",
            "patient_name",
            "doctor",
            "doctor_name",
            "start_at",
            "end_at",
            "status",
            "cancellation_reason",
            "cancelled_at",
        ]
        read_only_fields = fields

    def get_patient_name(self, appointment):
        return appointment.patient.get_full_name() or appointment.patient.username
