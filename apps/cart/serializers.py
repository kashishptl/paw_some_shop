from rest_framework import serializers
from .models import Cart, CartItem


# --------------------------------------------
# Cart Item Serializer
# --------------------------------------------

class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_image = serializers.ImageField(source='product.image', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id',
            'product',
            'product_name',
            'product_image',
            'quantity',
            'price_at_time',
            'subtotal'
        ]
        

    def get_subtotal(self, obj):
        return obj.quantity * obj.price_at_time


# --------------------------------------------
# Cart Serializer
# --------------------------------------------

class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = [
            'id',
            'user',
            'items',
            'total_items',
            'created_at'
        ]
        read_only_fields = ['user']

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())