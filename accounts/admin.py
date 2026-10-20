from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class PatientAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Patient details", {"fields": ("phone", "date_of_birth", "emergency_contact")}),
    )
    list_display = ("username", "email", "first_name", "last_name", "is_staff", "is_active")
