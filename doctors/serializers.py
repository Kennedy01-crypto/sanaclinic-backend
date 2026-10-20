from rest_framework import serializers

from .models import Doctor, WeeklySchedule


class WeeklyScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklySchedule
        fields = ["id", "weekday", "start_time", "end_time"]

    def validate(self, attrs):
        start_time = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end_time = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start_time is not None and end_time is not None:
            if start_time >= end_time:
                raise serializers.ValidationError({"end_time": "End time must be after start time."})
            if start_time.minute % 30 != 0 or end_time.minute % 30 != 0:
                raise serializers.ValidationError("Working periods must align to 30-minute slots.")
            if start_time.second or end_time.second:
                raise serializers.ValidationError("Working periods cannot contain seconds.")
        return attrs


class AdminScheduleSerializer(WeeklyScheduleSerializer):
    doctor = serializers.PrimaryKeyRelatedField(queryset=Doctor.objects.all())

    class Meta(WeeklyScheduleSerializer.Meta):
        fields = ["id", "doctor", "weekday", "start_time", "end_time"]


class DoctorSerializer(serializers.ModelSerializer):
    weekly_schedules = WeeklyScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Doctor
        fields = ["id", "name", "specialty", "active", "weekly_schedules"]
