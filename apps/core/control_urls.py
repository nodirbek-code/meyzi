from django.urls import path

from . import control, control_crud

urlpatterns = [
    path("manage/", control_crud.CrudIndexView.as_view(), name="control-manage"),
    path("manage/<str:res>/", control_crud.CrudListView.as_view(), name="control-manage-list"),
    path("manage/<str:res>/<int:pk>/", control_crud.CrudDetailView.as_view(), name="control-manage-detail"),
    path("login/", control.ControlLoginView.as_view(), name="control-login"),
    path("me/", control.ControlMeView.as_view(), name="control-me"),
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
