from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView, TokenObtainPairView
from drf_spectacular.utils import extend_schema, extend_schema_view

from appointments.models import Appointment
from doctors.models import Doctor

from .serializers import AdminPatientSerializer, ChangePasswordSerializer, ProfileUpdateSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


@extend_schema_view(post=extend_schema(tags=["Patient - Accounts"]))
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


@extend_schema_view(post=extend_schema(tags=["Patient - Accounts"]))
class CookieTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            access_token = response.data.get("access")
            refresh_token = response.data.get("refresh")
            response.set_cookie(
                key="access_token",
                value=access_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=60 * 15,
            )
            response.set_cookie(
                key="refresh_token",
                value=refresh_token,
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=60 * 60 * 24 * 7,
            )
            response.data = {"detail": "Signed in successfully."}
        return response


@extend_schema_view(post=extend_schema(tags=["Patient - Accounts"]))
class SwaggerTokenObtainPairView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []


@extend_schema_view(post=extend_schema(tags=["Patient - Accounts"]))
class CookieTokenRefreshView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token is missing."}, status=status.HTTP_401_UNAUTHORIZED)

        serializer = self.get_serializer(data={"refresh": refresh_token})
        serializer.is_valid(raise_exception=True)
        response = Response({"detail": "Session refreshed."}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=serializer.validated_data["access"],
            httponly=True,
            secure=not settings.DEBUG,
            samesite="Lax",
            max_age=60 * 15,
        )
        if "refresh" in serializer.validated_data:
            response.set_cookie(
                key="refresh_token",
                value=serializer.validated_data["refresh"],
                httponly=True,
                secure=not settings.DEBUG,
                samesite="Lax",
                max_age=60 * 60 * 24 * 7,
            )
        return response


@extend_schema_view(post=extend_schema(tags=["Patient - Accounts"]))
class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


@extend_schema_view(
    get=extend_schema(tags=["Patient - Accounts"]),
    put=extend_schema(tags=["Patient - Accounts"]),
    patch=extend_schema(tags=["Patient - Accounts"]),
)
class CurrentUserView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(
    put=extend_schema(tags=["Patient - Accounts"]),
    patch=extend_schema(tags=["Patient - Accounts"]),
)
class ProfileUpdateView(generics.UpdateAPIView):
    serializer_class = ProfileUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@extend_schema_view(patch=extend_schema(tags=["Patient - Accounts"]))
class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"detail": "Password updated successfully."}, status=status.HTTP_200_OK)


@extend_schema_view(get=extend_schema(tags=["Admin - Dashboard"]))
class AdminDashboardView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        now = timezone.now()
        appointments = (
            Appointment.objects.select_related("patient", "doctor")
            .order_by("-start_at")[:8]
        )
        recent_appointments = [
            {
                "id": appointment.id,
                "patient_name": appointment.patient.get_full_name() or appointment.patient.username,
                "doctor_name": appointment.doctor.name,
                "start_at": appointment.start_at.isoformat(),
                "status": appointment.status,
            }
            for appointment in appointments
        ]
        return Response(
            {
                "patients": User.objects.filter(is_staff=False, is_active=True).count(),
                "doctors": Doctor.objects.filter(active=True).count(),
                "upcoming_appointments": Appointment.objects.filter(
                    status=Appointment.STATUS_BOOKED,
                    start_at__gte=now,
                ).count(),
                "appointments_today": Appointment.objects.filter(
                    status=Appointment.STATUS_BOOKED,
                    start_at__date=timezone.localdate(),
                ).count(),
                "recent_appointments": recent_appointments,
            }
        )


@extend_schema_view(get=extend_schema(tags=["Admin - Patients"]))
class AdminPatientListView(generics.ListAPIView):
    serializer_class = AdminPatientSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter(is_staff=False).order_by("last_name", "first_name", "username")


@extend_schema_view(
    get=extend_schema(tags=["Admin - Patients"]),
    put=extend_schema(tags=["Admin - Patients"]),
    patch=extend_schema(tags=["Admin - Patients"]),
)
class AdminPatientDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = AdminPatientSerializer
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.filter(is_staff=False)
