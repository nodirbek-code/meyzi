from rest_framework import serializers


class PaymentMethodSerializer(serializers.Serializer):
    code = serializers.CharField()
    name = serializers.CharField()
    description = serializers.CharField()
    logo = serializers.CharField(allow_null=True, help_text="Logotip URL (fayl qo'yilmagan bo'lsa null)")
    enabled = serializers.BooleanField()
    status_text = serializers.CharField(help_text="Hozircha: 'Tez kunda'")
