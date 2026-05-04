from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny

from apps.products.models import Product, Rating
from apps.products.serializers import ProductSerializer, RatingSerializer


# -------------------------------
# PRODUCT LIST (USER + ADMIN)
# -------------------------------
class ProductListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminUser()]
        return [AllowAny()]

    # -------------------------------
    # GET PRODUCTS
    # -------------------------------
    def get(self, request):

        # 🔥 ADMIN: sees ALL products
        if request.user.is_authenticated and request.user.is_staff:
            products = Product.objects.all().select_related("category")

        # 🟢 USER: only active + in-stock products
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
    # CREATE PRODUCT (ADMIN ONLY)
    # -------------------------------
    def post(self, request):

        if not request.user.is_staff:
            return Response({
                "success": False,
                "message": "Only admin can add product"
            }, status=403)

        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
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
# PRODUCT DETAIL (VIEW / UPDATE / DELETE)
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

        # 🔴 USER restriction
        if not request.user.is_staff:
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
    # UPDATE PRODUCT (ADMIN ONLY)
    # -------------------------------
    def patch(self, request, id):

        if not request.user.is_staff:
            return Response({
                "success": False,
                "message": "Only admin can update product"
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
    # DELETE PRODUCT (ADMIN ONLY)
    # -------------------------------
    def delete(self, request, id):

        if not request.user.is_staff:
            return Response({
                "success": False,
                "message": "Only admin can delete product"
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
# PRODUCT RATING (USER ONLY)
# -------------------------------
class ProductRateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):

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