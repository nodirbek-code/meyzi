from rest_framework.routers import SimpleRouter

from .views import GuideBookingViewSet

router = SimpleRouter()
router.register("", GuideBookingViewSet, basename="guide-booking")

urlpatterns = router.urls
