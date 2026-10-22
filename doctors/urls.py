from django.urls import path

from .views import AdminDoctorDetailView, AdminDoctorListView, AdminScheduleDetailView, AdminScheduleListView, doctor_availability, doctor_detail, doctor_list, doctor_month_availability

urlpatterns = [
    path("admin/doctors/", AdminDoctorListView.as_view(), name="admin-doctor-list"),
    path("admin/doctors/<int:pk>/", AdminDoctorDetailView.as_view(), name="admin-doctor-detail"),
    path("admin/schedules/", AdminScheduleListView.as_view(), name="admin-schedule-list"),
    path("admin/schedules/<int:pk>/", AdminScheduleDetailView.as_view(), name="admin-schedule-detail"),
    path("", doctor_list, name="doctor-list"),
    path("<int:doctor_id>/availability/month/", doctor_month_availability, name="doctor-month-availability"),
    path("<int:doctor_id>/", doctor_detail, name="doctor-detail"),
    path("<int:doctor_id>/availability/", doctor_availability, name="doctor-availability"),
]
