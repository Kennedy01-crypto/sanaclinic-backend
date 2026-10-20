from django.contrib import admin

from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "patient", "doctor", "start_at", "end_at", "status")
    list_filter = ("status", "doctor")
    search_fields = ("patient__username", "patient__email", "doctor__name")
    readonly_fields = ("created_at", "updated_at")
