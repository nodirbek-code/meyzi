from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from .features import features


class _Lang(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()


class _Feature(serializers.Serializer):
    enabled = serializers.BooleanField()
    status_text = serializers.CharField()
    description = serializers.CharField()


class FeaturesSerializer(serializers.Serializer):
    languages = _Lang(many=True)
    default_language = serializers.CharField()
    ai_route = _Feature()
    multilingual_content = _Feature()
    payments = serializers.ListField(child=serializers.DictField())


class FeaturesView(APIView):
    """Platforma imkoniyatlari: tillar, AI marshrut, to'lov usullari ("Tez kunda" bo'lsa `enabled: false`)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=FeaturesSerializer)
    def get(self, request):
        return Response(features(request))
