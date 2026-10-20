from django.urls import path

from .views import AdminAppointmentCancelView, AdminAppointmentListView, cancel_appointment, create_appointment, patient_appointments, reschedule_appointment

urlpatterns = [
    path("admin/", AdminAppointmentListView.as_view(), name="admin-appointment-list"),
    path("admin/<int:appointment_id>/cancel/", AdminAppointmentCancelView.as_view(), name="admin-appointment-cancel"),
    path("", create_appointment, name="create-appointment"),
    path("<int:appointment_id>/cancel/", cancel_appointment, name="cancel-appointment"),
    path("<int:appointment_id>/reschedule/", reschedule_appointment, name="reschedule-appointment"),
    path("patients/<int:patient_id>/appointments/", patient_appointments, name="patient-appointments"),
]
