from rest_framework import serializers
from .models import User, Wishlist

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    role = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'password', 'role']

    def create(self, validated_data):
        validated_data['role'] = 'customer'  # 🔥 force role
        return User.objects.create_user(**validated_data)

    def create(self, validated_data):
        validated_data['role'] = 'customer'

        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password'],
            role=validated_data['role']
        )

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'profile_image', 'role','is_active', 'created_at']   

class WishlistSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    product_image = serializers.ImageField(source='product.image', read_only=True)

    class Meta:
        model = Wishlist
        fields = [
            'id',
            'product',
            'product_name',
            'product_price',
            'product_image',
            'created_at'
        ]


