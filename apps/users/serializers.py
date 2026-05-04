from rest_framework import serializers
from .models import User, Wishlist

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    

    class Meta:
        model = User
        fields = ['email', 'name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            name=validated_data['name'],
            password=validated_data['password']
        )


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'name', 'email', 'profile_image', 'role']   

class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wishlist
        fields = ['id', 'product', 'product_name', 'created_at']