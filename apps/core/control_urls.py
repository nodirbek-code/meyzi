from django.urls import path

from . import control, control_crud, control_import, control_media, control_photo_links, control_users

urlpatterns = [
    path("users/<int:pk>/", control_users.ControlUserView.as_view(), name="control-user"),
    path("users/<int:pk>/staff/", control_users.ControlUserStaffView.as_view(), name="control-user-staff"),
    path(
        "users/<int:pk>/<str:action>/",
        control_users.ControlUserBlockView.as_view(),
        name="control-user-block",
    ),
    path("media-import/", control_media.MediaImportListView.as_view(), name="control-media-import"),
    path(
        "media-import/<int:pk>/",
        control_media.MediaImportDetailView.as_view(),
        name="control-media-import-detail",
    ),
    path("manage/", control_crud.CrudIndexView.as_view(), name="control-manage"),
    path("manage/<str:res>/", control_crud.CrudListView.as_view(), name="control-manage-list"),
    path(
        "manage/<str:res>/import/template/",
        control_import.ImportTemplateView.as_view(),
        name="control-manage-import-template",
    ),
    path("manage/<str:res>/import/", control_import.ImportView.as_view(), name="control-manage-import"),
    path(
        "manage/<str:res>/photo-links/template/",
        control_photo_links.PhotoLinksTemplateView.as_view(),
        name="control-manage-photo-links-template",
    ),
    path(
        "manage/<str:res>/photo-links/",
        control_photo_links.PhotoLinksView.as_view(),
        name="control-manage-photo-links",
    ),
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
