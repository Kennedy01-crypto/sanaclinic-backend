from django.urls import path

from .views import AdminDashboardView, AdminPatientDetailView, AdminPatientListView, ChangePasswordView, CookieTokenObtainPairView, CookieTokenRefreshView, CurrentUserView, LogoutView, ProfileUpdateView, RegisterView, SwaggerTokenObtainPairView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", CookieTokenObtainPairView.as_view(), name="login"),
    path("token/", SwaggerTokenObtainPairView.as_view(), name="token-pair"),
    path("refresh/", CookieTokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("me/", CurrentUserView.as_view(), name="current-user"),
    path("profile/", ProfileUpdateView.as_view(), name="profile"),
    path("change-password/", ChangePasswordView.as_view(), name="change-password"),
    path("admin/summary/", AdminDashboardView.as_view(), name="admin-summary"),
    path("admin/patients/", AdminPatientListView.as_view(), name="admin-patient-list"),
    path("admin/patients/<int:pk>/", AdminPatientDetailView.as_view(), name="admin-patient-detail"),
]
