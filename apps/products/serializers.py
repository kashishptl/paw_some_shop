from rest_framework import serializers
from apps.products.models import Product, Rating
from apps.categories.models import Category


class RatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rating
        fields = "__all__"
        read_only_fields = ["user"]


class ProductSerializer(serializers.ModelSerializer):
    average_rating = serializers.SerializerMethodField()
    ratings = RatingSerializer(many=True, read_only=True)

    # input/output both use category name
    category = serializers.CharField()

    class Meta:
        model = Product
        fields = [
            "id",
            "category",
            "name",
            "description",
            "price",
            "stock",
            "image",
            "is_active",
            "created_at",
            "average_rating",
            "ratings",
        ]

    def get_average_rating(self, obj):
        return obj.get_average_rating()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["category"] = instance.category.name
        return data

    def validate_category(self, value):
        try:
            return Category.objects.get(name__iexact=value.strip())
        except Category.DoesNotExist:
            raise serializers.ValidationError("Category not found")

    def create(self, validated_data):
        category = validated_data.pop("category")
        return Product.objects.create(category=category, **validated_data)

    def update(self, instance, validated_data):
        category = validated_data.pop("category", None)

        if category:
            instance.category = category

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

    def validate_image(self, value):
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError("Image size should be less than 2MB")

        if value.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
            raise serializers.ValidationError("Only JPG, JPEG, PNG allowed")

        return value