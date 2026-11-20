from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import GuideViewSet, MyGuideProfileView

router = SimpleRouter()
router.register("", GuideViewSet, basename="guide")

urlpatterns = [
    path("me/", MyGuideProfileView.as_view(), name="guide-me"),
    *router.urls,
]
