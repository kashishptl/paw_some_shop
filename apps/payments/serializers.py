from rest_framework import serializers
from .models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    user_name = serializers.CharField(source="user.name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "order_id",
            "user",
            "user_name",
            "amount",
            "payment_method",
            "status",
            "transaction_id",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "amount",
            "status",
            "transaction_id",
            "created_at",
        ]