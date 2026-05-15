from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Category
from .serializers import CategorySerializer
from apps.products.models import Product
from apps.products.serializers import ProductSerializer


# --------------------------------------------
# Category List + Create
# --------------------------------------------

class CategoryListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):

        # 👑 Admin & Manager → ALL categories
        if request.user.is_authenticated and request.user.role in ["admin", "manager"]:
            categories = Category.objects.all()

        else:
            # 👤 Customer → only active categories
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

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can create category"
            }, status=403)

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
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]


    def patch(self, request, id):

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can update category"
            }, status=403)

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

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can delete category"
            }, status=403)

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

        # 👑 Admin & Manager → all products
        if request.user.is_authenticated and request.user.role in ["admin", "manager"]:

            products = Product.objects.filter(category=category)

        else:
            # 👤 Public/Customer → only active category + active products

            if not category.is_active:
                return Response({
                    "success": False,
                    "message": "Category not available"
                }, status=403)

            products = Product.objects.filter(
                category=category,
                category__is_active=True,
                is_active=True,
                stock__gt=0
            )

        serializer = ProductSerializer(
            products,
            many=True,
            context={"request": request}
        )

        return Response({
            "success": True,
            "category": category.name,
            "product_count": products.count(),
            "data": serializer.data
        })