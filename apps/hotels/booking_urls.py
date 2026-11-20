from rest_framework.routers import SimpleRouter

from .views import HotelBookingViewSet

router = SimpleRouter()
router.register("", HotelBookingViewSet, basename="hotel-booking")

urlpatterns = router.urls
