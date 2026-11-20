from rest_framework import permissions, viewsets

from .models import Article, FaqItem, Page
from .serializers import ArticleDetailSerializer, ArticleListSerializer, FaqItemSerializer, PageSerializer


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """Qo'llanmalar (blog). Filtr: ?destination=<slug>&search=..."""

    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    search_fields = ["title", "excerpt", "body"]

    def get_queryset(self):
        qs = Article.objects.filter(status=Article.Status.PUBLISHED).select_related("destination")
        if destination := self.request.query_params.get("destination"):
            qs = qs.filter(destination__slug=destination)
        return qs

    def get_serializer_class(self):
        return ArticleDetailSerializer if self.action == "retrieve" else ArticleListSerializer


class FaqViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = FaqItemSerializer
    pagination_class = None
    queryset = FaqItem.objects.filter(is_active=True)


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """Sahifalar: /pages/terms/, /pages/privacy/ ..."""

    permission_classes = [permissions.AllowAny]
    serializer_class = PageSerializer
    lookup_field = "slug"
    pagination_class = None
    queryset = Page.objects.filter(is_published=True)
