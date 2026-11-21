from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="auth-register"),
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
    path("me/", views.MeView.as_view(), name="auth-me"),
    path("me/password/", views.ChangePasswordView.as_view(), name="auth-change-password"),
    path("password/forgot/", views.PasswordForgotView.as_view(), name="auth-password-forgot"),
    path("password/reset/", views.PasswordResetView.as_view(), name="auth-password-reset"),
    path("email/send-code/", views.EmailSendCodeView.as_view(), name="auth-email-send-code"),
    path("email/verify/", views.EmailVerifyView.as_view(), name="auth-email-verify"),
    path("phone/request-code/", views.PhoneRequestCodeView.as_view(), name="auth-phone-request"),
    path("phone/verify/", views.PhoneVerifyView.as_view(), name="auth-phone-verify"),
    path("me/phone/request-code/", views.MePhoneRequestCodeView.as_view(), name="auth-me-phone-request"),
    path("me/phone/verify/", views.MePhoneVerifyView.as_view(), name="auth-me-phone-verify"),
    path("phone-check/send-code/", views.PhoneCheckRequestCodeView.as_view(), name="auth-phone-check-send"),
    path("phone-check/verify/", views.PhoneCheckVerifyView.as_view(), name="auth-phone-check-verify"),
    path("google/", views.GoogleLoginView.as_view(), name="auth-google"),
]
