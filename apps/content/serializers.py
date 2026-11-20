from rest_framework import serializers

from apps.catalog.serializers import DestinationShortSerializer
from apps.tours.serializers import TourCardSerializer

from .models import Article, FaqItem, Page


class ArticleListSerializer(serializers.ModelSerializer):
    destination = DestinationShortSerializer(read_only=True)

    class Meta:
        model = Article
        fields = ["id", "title", "slug", "excerpt", "cover", "destination", "published_at"]


class ArticleDetailSerializer(ArticleListSerializer):
    tours = serializers.SerializerMethodField()

    class Meta(ArticleListSerializer.Meta):
        fields = ArticleListSerializer.Meta.fields + ["body", "tours"]

    def get_tours(self, article) -> list[dict]:
        from apps.tours.views import public_tours

        qs = public_tours().filter(articles=article).select_related("destination", "agency")
        qs = qs.prefetch_related("categories", "media")
        return TourCardSerializer(qs, many=True, context=self.context).data


class FaqItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaqItem
        fields = ["id", "question", "answer"]


class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = ["slug", "title", "body", "updated_at"]
