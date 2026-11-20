from rest_framework.routers import SimpleRouter

from .views import AgencyApplicationViewSet, AgencyViewSet

router = SimpleRouter()
router.register("applications", AgencyApplicationViewSet, basename="agency-application")
router.register("", AgencyViewSet, basename="agency")

urlpatterns = router.urls
