from django.contrib import admin

from .models import Doctor, WeeklySchedule


class WeeklyScheduleInline(admin.TabularInline):
    model = WeeklySchedule
    extra = 1


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("name", "specialty", "active")
    list_filter = ("active",)
    search_fields = ("name", "specialty")
    inlines = (WeeklyScheduleInline,)
