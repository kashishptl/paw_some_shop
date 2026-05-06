from urllib import request

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import User, Wishlist
from .serializers import SignupSerializer, UserSerializer, WishlistSerializer
from apps.products.models import Product

from .permissions import IsAdmin, IsManagerOrAdmin

User = get_user_model()


# =========================
# signup view
# =========================

class SignupView(APIView):
    permission_classes = []
    def post(self, request):
        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # 🔥 Generate tokens
            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "User created successfully",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# =========================
# login view
# =========================

class LoginView(APIView):
    permission_classes = []
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = User.objects.filter(email=email).first()

        if user and user.check_password(password):

            refresh = RefreshToken.for_user(user)

            return Response({
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role
                }
            })

        return Response({"error": "Invalid credentials"}, status=401)

# =========================
# profile view
# =========================

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

# =========================
# Add wishlist view
# =========================

class AddToWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "customer":
            return Response({"error": "Only customers can add to wishlist"}, status=403)

        product_id = request.data.get("product_id")

        product = get_object_or_404(Product, id=product_id)

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return Response({"message": "Added to wishlist"})
        else:
            return Response({"message": "Already in wishlist"})


# =========================
# remove from wishlist view
# =========================

class RemoveFromWishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):

        if request.user.role != "customer":
            return Response({"error": "Only customers can remove wishlist"}, status=403)
        

        Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()


        return Response({"message": "Removed from wishlist"})

# =========================
# wishlist view
# =========================

class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        if request.user.role != "customer":
            return Response({"error": "Only customers can view wishlist"}, status=403)

        items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(items, many=True)
        return Response(serializer.data)

# =========================
# ADMIN ASSIGN ROLE VIEW
# =========================

class AssignRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, user_id):
        user = User.objects.get(id=user_id)

        role = request.data.get("role")

        if role not in ["admin", "manager", "customer"]:
            return Response({"error": "Invalid role"}, status=400)

        user.role = role
        user.save()

        return Response({"message": f"Role updated to {role}"})