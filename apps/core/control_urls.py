from django.urls import path

from . import control

urlpatterns = [
    path("login/", control.ControlLoginView.as_view(), name="control-login"),
    path("dashboard/", control.ControlDashboardView.as_view(), name="control-dashboard"),
    path(
        "items/guide/<int:pk>/certificate/",
        control.ControlCertificateView.as_view(),
        name="control-certificate",
    ),
    path("items/<str:kind>/", control.ControlListView.as_view(), name="control-list"),
    path("items/<str:kind>/<int:pk>/", control.ControlItemView.as_view(), name="control-item"),
    path(
        "items/<str:kind>/<int:pk>/<str:action>/", control.ControlActionView.as_view(), name="control-action"
    ),
]
