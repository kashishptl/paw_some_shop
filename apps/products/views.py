from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.products.models import Product, Rating
from apps.products.serializers import ProductSerializer, RatingSerializer

from django.shortcuts import get_object_or_404


# -------------------------------
# HELPER FUNCTION
# -------------------------------

def is_admin_or_manager(user):
    return user.is_authenticated and (
        user.is_staff or user.role in ["admin", "manager"]
    )


# -------------------------------
# PRODUCT LIST
# -------------------------------

class ProductListCreateView(APIView):

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):

        # Admin + Manager see all products
        if is_admin_or_manager(request.user):
            products = Product.objects.all().select_related("category")

        # Customer/Public see only active products
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

    def post(self, request):

        if not is_admin_or_manager(request.user):
            return Response({
                "success": False,
                "message": "Only admin or manager can add product"
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
# PRODUCT DETAIL
# -------------------------------

class ProductDetailView(APIView):

    def get_permissions(self):
        if self.request.method in ["PATCH", "DELETE"]:
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request, id):
        product = get_object_or_404(Product, id=id)

        # normal user cannot view inactive product
        if not is_admin_or_manager(request.user):
            if not product.is_active or not product.category.is_active:
                return Response({
                    "success": False,
                    "message": "Product not found"
                }, status=404)

        serializer = ProductSerializer(product, context={"request": request})

        return Response({
            "success": True,
            "data": serializer.data
        })

    def patch(self, request, id):
        if not is_admin_or_manager(request.user):
            return Response({
                "success": False,
                "message": "Only admin or manager can update product"
            }, status=403)

        product = get_object_or_404(Product, id=id)
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

    def delete(self, request, id):
        if not is_admin_or_manager(request.user):
            return Response({
                "success": False,
                "message": "Only admin or manager can delete product"
            }, status=403)

        product = get_object_or_404(Product, id=id)
        product.delete()

        return Response({
            "success": True,
            "message": "Product deleted successfully"
        })

# -------------------------------
# PRODUCT RATING
# -------------------------------

class ProductRateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        product = get_object_or_404(Product, id=id)

        rating = request.data.get("rating")
        review = request.data.get("review", "")

        if rating is None:
            return Response({"success": False, "message": "Rating is required"}, status=400)

        rating = int(rating)

        rating_obj = Rating.objects.filter(
            product=product,
            user=request.user
        ).first()

        if rating_obj:
            rating_obj.rating = rating
            rating_obj.review = review
            rating_obj.save()
        else:
            rating_obj = Rating.objects.create(
                product=product,
                user=request.user,
                rating=rating,
                review=review
            )

        serializer = RatingSerializer(rating_obj)

        return Response({
            "success": True,
            "message": "Rating submitted successfully",
            "data": serializer.data
        }, status=201)


# -------------------------------
# PRODUCT RATINGS LIST
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