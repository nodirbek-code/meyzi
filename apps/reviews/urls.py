from rest_framework.routers import SimpleRouter

from .views import MyReviewViewSet, ReviewViewSet

router = SimpleRouter()
router.register("my", MyReviewViewSet, basename="my-review")
router.register("", ReviewViewSet, basename="review")

urlpatterns = router.urls
