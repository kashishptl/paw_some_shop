from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from apps.orders.serializers import OrderSerializer
from rest_framework.permissions import IsAuthenticated
from .models import Order, OrderItem
from apps.products.models import Product
from apps.cart.models import CartItem

# -------------------------------
# CREATE ORDER (USER ONLY)
# -------------------------------
permission_classes = [IsAuthenticated]

class CreateOrderView(APIView):
    def post(self, request):
        user = request.user

        cart_items = CartItem.objects.filter(user=user)

        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        total_amount = 0
        order = Order.objects.create(user=user, total_amount=0)

        for item in cart_items:
            product = item.product
            quantity = item.quantity

            # ✅ STOCK CHECK
            if quantity > product.stock:
                order.delete()  # rollback
                return Response({
                    "error": f"Only {product.stock} items available for {product.name}"
                }, status=400)

            price = product.price
            total_amount += price * quantity

            # Create order item
            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                price=price
            )

            # ✅ REDUCE STOCK
            product.stock -= quantity
            product.save()

        order.total_amount = total_amount
        order.save()

        # Clear cart
        cart_items.delete()

        return Response({"message": "Order created successfully"}, status=201)
    
# -------------------------------
# Get All Orders
# -------------------------------

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)
    
# -------------------------------
# Single Order
# -------------------------------

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        serializer = OrderSerializer(order)
        return Response(serializer.data)
    
# -------------------------------
# Cancel Order
# -------------------------------

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)

        if order.status == "delivered":
            return Response({"error": "Cannot cancel delivered order"}, status=400)

        order.status = "cancelled"
        order.save()

        return Response({"message": "Order cancelled"})

# -------------------------------
# Admin Update Status
# -------------------------------

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        order = get_object_or_404(Order, id=id)

        new_status = request.data.get("status")

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({"error": "Invalid status"}, status=400)

        order.status = new_status
        order.save()

        return Response({"message": "Status updated"})