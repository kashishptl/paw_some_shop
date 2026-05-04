from rest_framework import serializers
from apps.products.models import Product, Rating


class RatingSerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, required=False)
    class Meta:
        model = Rating
        fields = '__all__'
        read_only_fields = ['user']

class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    ratings = RatingSerializer(many=True, read_only=True)

    class Meta:
        model = Product
        fields = '__all__'

    def get_average_rating(self, obj):
        return obj.get_average_rating()
    
        # -------------------------------
    # Image validation
    # -------------------------------
    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError("Image is required")

        # file size check (optional)
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Image size should be less than 2MB")

        # file type check (optional)
        if not value.content_type in ["image/jpeg", "image/png", "image/jpg"]:
            raise serializers.ValidationError("Only JPG, JPEG, PNG allowed")

        return value