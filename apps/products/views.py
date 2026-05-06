from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.products.models import Product, Rating
from apps.products.serializers import ProductSerializer, RatingSerializer


# -------------------------------
# PRODUCT LIST + CREATE
# -------------------------------
class ProductListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    # -------------------------------
    # GET PRODUCTS
    # -------------------------------
    def get(self, request):

        # 👑 Admin & Manager → ALL products
        if request.user.is_authenticated and request.user.role in ["admin", "manager"]:
            products = Product.objects.all().select_related("category")

        # 🛒 Customer → only active products
        else:
            products = Product.objects.filter(
                category__is_active=True,
                is_active=True
            ).select_related("category")

        serializer = ProductSerializer(products, many=True)

        return Response({
            "success": True,
            "count": products.count(),
            "data": serializer.data
        })


    # -------------------------------
    # CREATE PRODUCT (ADMIN + MANAGER)
    # -------------------------------
    def post(self, request):

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can add product"
            }, status=403)

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save(created_by=request.user)  # 🔥 track creator
            return Response({
                "success": True,
                "message": "Product created successfully",
                "data": serializer.data
            }, status=201)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)


# -------------------------------
# PRODUCT DETAIL
# -------------------------------
class ProductDetailView(APIView):

    # -------------------------------
    # GET SINGLE PRODUCT
    # -------------------------------
    def get(self, request, id):
        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found"
            }, status=404)

        # 🛒 Customer restriction
        if request.user.role == "customer":
            if not product.is_active or product.stock <= 0:
                return Response({
                    "success": False,
                    "message": "Product not available"
                }, status=403)

        serializer = ProductSerializer(product)

        return Response({
            "success": True,
            "data": serializer.data
        })


    # -------------------------------
    # UPDATE PRODUCT (ADMIN + MANAGER)
    # -------------------------------
    def patch(self, request, id):

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can update product"
            }, status=403)

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found"
            }, status=404)

        serializer = ProductSerializer(product, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({
                "success": True,
                "message": "Product updated successfully",
                "data": serializer.data
            })

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=400)


    # -------------------------------
    # DELETE PRODUCT (ADMIN ONLY and manager)
    # -------------------------------
    def delete(self, request, id):

        if request.user.role not in ["admin", "manager"]:
            return Response({
                "success": False,
                "message": "Only admin or manager can delete product"
            }, status=403)

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found"
            }, status=404)

        product.delete()

        return Response({
            "success": True,
            "message": "Product deleted successfully"
        }, status=204)


# -------------------------------
# PRODUCT RATING (CUSTOMER ONLY)
# -------------------------------
class ProductRateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):

        if request.user.role != "customer":
            return Response({
                "success": False,
                "message": "Only customers can rate products"
            }, status=403)

        try:
            product = Product.objects.get(id=id)
        except Product.DoesNotExist:
            return Response({
                "success": False,
                "message": "Product not found"
            }, status=404)

        rating_obj, created = Rating.objects.get_or_create(
            product=product,
            user=request.user
        )

        rating_obj.rating = request.data.get("rating")
        rating_obj.review = request.data.get("review", "")
        rating_obj.save()

        return Response({
            "success": True,
            "message": "Rating submitted successfully"
        })


# -------------------------------
# PRODUCT RATINGS LIST (PUBLIC)
# -------------------------------
class ProductRatingListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, id):

        ratings = Rating.objects.filter(product_id=id)
        serializer = RatingSerializer(ratings, many=True)

        return Response({
            "success": True,
            "count": ratings.count(),
            "data": serializer.data
        })