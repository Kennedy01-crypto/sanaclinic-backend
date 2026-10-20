from django.core.exceptions import ValidationError
from django.db import models


WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


class Doctor(models.Model):
    name = models.CharField(max_length=120)
    specialty = models.CharField(max_length=120, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class WeeklySchedule(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="weekly_schedules")
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.CheckConstraint(check=models.Q(start_time__lt=models.F("end_time")), name="schedule_start_before_end"),
        ]

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Work period end time must be after the start time.")
        if self.start_time.minute % 30 != 0 or self.end_time.minute % 30 != 0:
            raise ValidationError("Working periods must align to 30-minute slots.")
        if self.start_time.second or self.end_time.second:
            raise ValidationError("Working periods cannot contain seconds.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor.name} - {self.get_weekday_display()} {self.start_time} to {self.end_time}"
