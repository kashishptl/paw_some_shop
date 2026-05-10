from rest_framework import serializers


class DashboardCardSerializer(serializers.Serializer):
    total_sales = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_products = serializers.IntegerField()
    total_categories = serializers.IntegerField()


class OrdersSummarySerializer(serializers.Serializer):
    pending = serializers.IntegerField()
    delivered = serializers.IntegerField()
    cancelled = serializers.IntegerField()


class RecentOrderSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order_number = serializers.CharField()
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()
    status = serializers.CharField()
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    created_at = serializers.DateTimeField()


class LowStockProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    stock = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)


class TopProductSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_reviews = serializers.IntegerField()


class AdminDashboardSerializer(serializers.Serializer):
    cards = DashboardCardSerializer()
    orders_summary = OrdersSummarySerializer()
    recent_orders = RecentOrderSerializer(many=True)
    low_stock_products = LowStockProductSerializer(many=True)
    top_products = TopProductSerializer(many=True)