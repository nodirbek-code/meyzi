from django.urls import path

from .views import PaymentMethodsView

urlpatterns = [
    path("methods/", PaymentMethodsView.as_view(), name="payment-methods"),
]
