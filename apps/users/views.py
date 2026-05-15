from urllib import request

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from apps.cart.models import CartItem
from apps.orders.models import Order
from apps.orders.serializers import OrderSerializer
from django.db.models import Sum, F

from .models import User, Wishlist
from .serializers import SignupSerializer, UserSerializer, WishlistSerializer
from apps.products.models import Product
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .permissions import IsAdmin, IsManagerOrAdmin

from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
User = get_user_model()


# =========================
# verify email
# =========================

class VerifyEmailView(APIView):
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except Exception:
            return Response({
                "error": "Invalid verification link"
            }, status=status.HTTP_400_BAD_REQUEST)

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()

            return Response({
                "message": "Email verified successfully. Now you can login."
            }, status=status.HTTP_200_OK)

        return Response({
            "error": "Verification link is invalid or expired"
        }, status=status.HTTP_400_BAD_REQUEST)

# =========================
# signup view
# =========================

class SignupView(APIView):
    permission_classes = []

    def post(self, request):
        password = request.data.get("password")

        # Strong password validation
        try:
            validate_password(password)
        except ValidationError as e:
            return Response({
                "password_errors": e.messages
            }, status=status.HTTP_400_BAD_REQUEST)

        serializer = SignupSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            # User inactive until email verified
            user.is_active = False
            user.save()

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)

            verification_link = request.build_absolute_uri(
                f"/api/users/verify-email/{uid}/{token}/"
            )

            send_mail(
                subject="Verify your email",
                message=f"Click this link to verify your email:\n{verification_link}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )

            return Response({
                "message": "User created successfully. Verification link sent to email.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "role": user.role,
                    "is_active": user.is_active
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

        if not user:
            return Response({
                "error": "Email not registered"
            }, status=404)

        if not user.check_password(password):
            return Response({
                "error": "Wrong password"
            }, status=401)

        if user.is_active == False:
            return Response({
                "error": "Please verify your email before login"
            }, status=403)

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "is_active": user.is_active,
                "role": user.role
            }
        })
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
# Wishlist View
# GET    → view wishlist
# POST   → add to wishlist
# DELETE → remove from wishlist
# =========================

class WishlistView(APIView):
    permission_classes = [IsAuthenticated]

    # View wishlist
    def get(self, request):
        items = Wishlist.objects.filter(user=request.user)
        serializer = WishlistSerializer(items, many=True)

        return Response({
            "success": True,
            "count": items.count(),
            "data": serializer.data
        })

    # Add to wishlist
    def post(self, request):
        product_id = request.data.get("product_id")

        if not product_id:
            return Response({
                "success": False,
                "message": "product_id is required"
            }, status=400)

        product = get_object_or_404(Product, id=product_id)

        wishlist, created = Wishlist.objects.get_or_create(
            user=request.user,
            product=product
        )

        if created:
            return Response({
                "success": True,
                "message": "Added to wishlist"
            }, status=201)

        return Response({
            "success": False,
            "message": "Already in wishlist"
        }, status=200)

    # Remove from wishlist
class WishlistRemoveView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        deleted_count, _ = Wishlist.objects.filter(
            user=request.user,
            product_id=product_id
        ).delete()

        if deleted_count == 0:
            return Response({
                "success": False,
                "message": "Product not found in wishlist"
            }, status=404)

        return Response({
            "success": True,
            "message": "Removed from wishlist"
        }, status=200)
# =========================
# ADMIN ASSIGN ROLE VIEW
# =========================

class AssignRoleView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    # -------------------------------
    # UPDATE ROLE / ACTIVE STATUS
    # -------------------------------
    def patch(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        role = request.data.get("role")

        if role:
            if role not in ["admin", "manager", "customer"]:
                return Response(
                    {"error": "Invalid role"},
                    status=400
                )

            user.role = role

        if "is_active" in request.data:
            is_active = request.data.get("is_active")

            if isinstance(is_active, bool):
                user.is_active = is_active

            elif str(is_active).lower() == "true":
                user.is_active = True

            elif str(is_active).lower() == "false":
                user.is_active = False

            else:
                return Response(
                    {"error": "is_active must be true or false"},
                    status=400
                )

        user.save()

        return Response({
            "success": True,
            "message": "User updated successfully",
            "data": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "is_active": user.is_active
            }
        })

    # -------------------------------
    # DELETE USER
    # -------------------------------
    def delete(self, request, user_id):
        user = get_object_or_404(User, id=user_id)

        # Prevent deleting self
        if user == request.user:
            return Response({
                "success": False,
                "message": "You cannot delete yourself"
            }, status=400)

        user.delete()

        return Response({
            "success": True,
            "message": "User deleted successfully"
        }, status=200)


# =========================
# USER DASHBOARD VIEW
# =========================

class UserDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        total_orders = Order.objects.filter(user=user).count()
        pending_orders = Order.objects.filter(user=user, status="pending").count()
        delivered_orders = Order.objects.filter(user=user, status="delivered").count()
        cancelled_orders = Order.objects.filter(user=user, status="cancelled").count()

        cart_items = CartItem.objects.filter(cart__user=user)

        cart_items_count = cart_items.count()
        cart_total = cart_items.aggregate(
            total=Sum(F("quantity") * F("price_at_time"))
        )["total"] or 0

        wishlist_count = Wishlist.objects.filter(user=user).count()

        recent_orders = Order.objects.filter(user=user).order_by("-created_at")[:5]

        return Response({
            "success": True,
            "profile": UserSerializer(user, context={"request": request}).data,
            "summary": {
                "total_orders": total_orders,
                "pending_orders": pending_orders,
                "delivered_orders": delivered_orders,
                "cancelled_orders": cancelled_orders,
                "cart_items_count": cart_items_count,
                "cart_total": cart_total,
                "wishlist_count": wishlist_count,
            },
            "recent_orders": OrderSerializer(recent_orders, many=True).data
        })
    


class VerifyEmailView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = User.objects.get(pk=uid)
        except Exception:
            return render(request, "email_verification.html", {
                "success": False,
                "message": "Invalid verification link."
            })

        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.is_email_verified = True
            user.save()

            return render(request, "email_verification.html", {
                "success": True,
                "message": "Email verified successfully. Now you can login."
            })

        return render(request, "email_verification.html", {
            "success": False,
            "message": "Verification link expired or invalid."
        })