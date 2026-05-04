from rest_framework import serializers
from .models import Category


class CategorySerializer(serializers.ModelSerializer):
    is_active = serializers.BooleanField(default=True, required=False)
    
    class Meta:
        model = Category
        fields = "__all__"

    def validate_name(self, value):
        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError("Category name is too short")

        return value

    def validate_slug(self, value):
        value = value.strip()

        if " " in value:
            raise serializers.ValidationError("Slug must not contain spaces")

        if value != value.lower():
            raise serializers.ValidationError("Slug must be lowercase")

        return value