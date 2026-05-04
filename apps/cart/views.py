from itertools import product

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import F, Sum
from django.db import transaction

from .models import Cart, CartItem
from .serializers import CartSerializer
from apps.products.models import Product


# --------------------------------------------
# Cart View
# --------------------------------------------

class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        items = cart.items.select_related('product')

        total = items.aggregate(
            total=Sum(F('quantity') * F('price_at_time'))
        )['total'] or 0

        serializer = CartSerializer(cart)

        return Response({
            "success": True,
            "cart": serializer.data,
            "total_price": total
        })


# --------------------------------------------
# ADD TO CART
# --------------------------------------------

class AddToCartView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        product_id = request.data.get('product_id')

        # ✅ Safe quantity
        try:
            quantity = int(request.data.get('quantity', 1))
        except:
            return Response({"success": False, "error": "Invalid quantity"}, status=400)

        if quantity <= 0:
            return Response({"success": False, "error": "Quantity must be > 0"}, status=400)

        # ✅ Product check
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({"success": False, "error": "Product not found"}, status=404)

        # ❌ Inactive product
        if not product.is_active:
            return Response({"success": False, "error": "Product not available"}, status=400)

        # ❌ Out of stock product
        if product.stock <= 0:
            return Response({
                "success": False,
                "error": "Product out of stock"
            }, status=400)

        # ❌ Quantity check
        if quantity > product.stock:
            return Response({
                "success": False,
                "error": f"Only {product.stock} items available"
            }, status=400)
        

        cart, _ = Cart.objects.get_or_create(user=request.user)

        item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={"price_at_time": product.price}
        )

        # ✅ If already exists
        if not created:
            if item.quantity + quantity > product.stock:
                return Response({
                    "success": False,
                    "error": f"Only {product.stock - item.quantity} more allowed"
                }, status=400)

            item.quantity += quantity
            item.save()

        return Response({
            "success": True,
            "message": "Product added to cart"
        })


# --------------------------------------------
# UPDATE CART
# --------------------------------------------

class UpdateCartView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request):
        product_id = request.data.get('product_id')

        try:
            quantity = int(request.data.get('quantity'))
        except:
            return Response({"success": False, "error": "Invalid quantity"}, status=400)

        if quantity < 0:
            return Response({"success": False, "error": "Quantity cannot be negative"}, status=400)

        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({"success": False, "error": "Item not found"}, status=404)

        product = item.product

        # ❌ Stock check
        if quantity > product.stock:
            return Response({
                "success": False,
                "error": f"Only {product.stock} items available"
            }, status=400)

        # ✅ Auto remove if 0
        if quantity == 0:
            item.delete()
            return Response({
                "success": True,
                "message": "Item removed"
            })

        item.quantity = quantity
        item.save()

        return Response({
            "success": True,
            "message": "Quantity updated"
        })


# --------------------------------------------
# REMOVE FROM CART
# --------------------------------------------

class RemoveFromCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        try:
            item = CartItem.objects.get(cart=cart, product_id=product_id)
        except CartItem.DoesNotExist:
            return Response({"success": False, "error": "Item not found"}, status=404)

        item.delete()

        return Response({
            "success": True,
            "message": "Item removed"
        })


# --------------------------------------------
# CLEAR CART
# --------------------------------------------

class ClearCartView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)

        cart.items.all().delete()

        return Response({
            "success": True,
            "message": "Cart cleared"
        })