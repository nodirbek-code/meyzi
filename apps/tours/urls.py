from rest_framework.routers import SimpleRouter

from .views import TourCategoryViewSet, TourViewSet

router = SimpleRouter()
router.register("categories", TourCategoryViewSet, basename="tour-category")
router.register("", TourViewSet, basename="tour")

urlpatterns = router.urls
