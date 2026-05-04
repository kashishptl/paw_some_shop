from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from .models import Category
from .serializers import CategorySerializer
from apps.products.models import Product
from apps.products.serializers import ProductSerializer


# --------------------------------------------
# Category List + Create
# --------------------------------------------

class CategoryListCreateView(APIView):

    def get_permissions(self):
        # 🔐 Only admin can create
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        # 👤 Everyone can view
        return [AllowAny()]

    def get(self, request):

        # 👑 Admin sees ALL categories
        if request.user.is_authenticated and request.user.is_staff:
            categories = Category.objects.all()
        else:
            # 👤 User sees only active categories
            categories = Category.objects.filter(
                products__is_active=True
            ).distinct()

        serializer = CategorySerializer(categories, many=True)

        return Response({
            "success": True,
            "count": categories.count(),
            "data": serializer.data
        })

    def post(self, request):
        serializer = CategorySerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Category created successfully",
                "data": serializer.data
            }, status=201)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)


# --------------------------------------------
# Category Detail (Update & Delete)
# --------------------------------------------

class CategoryDetailView(APIView):

    def get_permissions(self):
        # 🔐 Only admin can update/delete
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated(), IsAdminUser()]
        return [AllowAny()]

    def patch(self, request, id):
        try:
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response({
                "success": False,
                "message": "Category not found"
            }, status=404)

        serializer = CategorySerializer(category, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Category updated successfully",
                "data": serializer.data
            })

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)

    def delete(self, request, id):
        try:
            category = Category.objects.get(id=id)
        except Category.DoesNotExist:
            return Response({
                "success": False,
                "message": "Category not found"
            }, status=404)

        category.delete()

        return Response({
            "success": True,
            "message": "Category deleted successfully"
        })


# --------------------------------------------
# Category Products View
# --------------------------------------------

class CategoryProductsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        try:
            category = Category.objects.get(slug=slug)
        except Category.DoesNotExist:
            return Response({
                "success": False,
                "message": "Category not found"
            }, status=404)

        # 🔴 Hide inactive category from normal users
        if not category.is_active:
            if not (request.user.is_authenticated and request.user.is_staff):
                return Response({
                    "success": False,
                    "message": "Category not available"
                }, status=403)

        # 👑 Admin sees all products
        if request.user.is_authenticated and request.user.is_staff:
            products = Product.objects.filter(category=category)

        else:
            # 👤 Users see only active + in-stock products
            products = Product.objects.filter(
                category__is_active=True,
                category=category,
                is_active=True
            )

        serializer = ProductSerializer(products, many=True)

        return Response({
            "success": True,
            "category": category.name,
            "product_count": products.count(),
            "data": serializer.data
        })