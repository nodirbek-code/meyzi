from drf_spectacular.utils import extend_schema
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from . import methods
from .serializers import PaymentMethodSerializer


class PaymentMethodsView(APIView):
    """To'lov usullari (Payme, Click, Uzum Nasiya). Hozircha barchasi "Tez kunda" (`enabled: false`)."""

    permission_classes = [permissions.AllowAny]

    @extend_schema(responses=PaymentMethodSerializer(many=True))
    def get(self, request):
        return Response(methods.available_methods(request))
