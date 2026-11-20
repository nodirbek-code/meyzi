from django.urls import path
from rest_framework.routers import SimpleRouter

from .views import HotelViewSet, MyHotelView

router = SimpleRouter()
router.register("", HotelViewSet, basename="hotel")

urlpatterns = [
    path("me/", MyHotelView.as_view(), name="hotel-me"),
    *router.urls,
]
