from rest_framework.routers import SimpleRouter

from .views import ArticleViewSet, FaqViewSet, PageViewSet

router = SimpleRouter()
router.register("articles", ArticleViewSet, basename="article")
router.register("faq", FaqViewSet, basename="faq")
router.register("pages", PageViewSet, basename="page")

urlpatterns = router.urls
