from email.headerregistry import Address

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction

from apps.orders.serializers import AddressSerializer, OrderSerializer
from .models import Order, OrderItem
from apps.cart.models import CartItem
from .models import Order, OrderItem, Address

# -------------------------------
# CREATE ORDER (USER ONLY)
# -------------------------------

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        cart_items = CartItem.objects.filter(
            cart__user=user
        ).select_related("product")

        if not cart_items.exists():
            return Response({
                "error": "Cart is empty"
            }, status=status.HTTP_400_BAD_REQUEST)

        address_id = request.data.get("address_id")

        if not address_id:
            return Response({
                "error": "address_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        address = get_object_or_404(
            Address,
            id=address_id,
            user=user
        )

        payment_method = request.data.get("payment_method", "cod")

        with transaction.atomic():

            order = Order.objects.create(
                user=user,

                address_ref=address,

                full_name=address.full_name,
                email=address.email,
                address=address.address,
                city=address.city,
                zip_code=address.zip_code,
                country=address.country,
                phone=address.phone,

                subtotal=0,
                tax=0,
                shipping_charge=0,
                total_amount=0,

                payment_method=payment_method
            )

            subtotal = 0

            for item in cart_items:
                product = item.product
                quantity = item.quantity

                if quantity > product.stock:
                    transaction.set_rollback(True)

                    return Response({
                        "error": f"Only {product.stock} items available for {product.name}"
                    }, status=status.HTTP_400_BAD_REQUEST)

                price = product.price
                subtotal += price * quantity

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=price
                )

                product.stock -= quantity
                product.save()

            tax = 0
            shipping_charge = 0

            order.subtotal = subtotal
            order.tax = tax
            order.shipping_charge = shipping_charge
            order.total_amount = subtotal + tax + shipping_charge

            order.save()

            cart_items.delete()

        serializer = OrderSerializer(order)

        return Response({
            "success": True,
            "message": "Order created successfully",
            "order": serializer.data
        }, status=status.HTTP_201_CREATED)


# -------------------------------
# GET USER ORDERS
# -------------------------------

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user).order_by("-created_at")
        serializer = OrderSerializer(orders, many=True)

        return Response({
            "success": True,
            "orders": serializer.data
        }, status=status.HTTP_200_OK)


# -------------------------------
# SINGLE ORDER
# -------------------------------

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)
        serializer = OrderSerializer(order)

        return Response({
            "success": True,
            "order": serializer.data
        }, status=status.HTTP_200_OK)


# -------------------------------
# CANCEL ORDER
# -------------------------------

class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        order = get_object_or_404(Order, id=id, user=request.user)

        if order.status == "delivered":
            return Response({
                "error": "Cannot cancel delivered order"
            }, status=status.HTTP_400_BAD_REQUEST)

        if order.status == "cancelled":
            return Response({
                "error": "Order already cancelled"
            }, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Restore stock after cancellation
            for item in order.items.all():
                product = item.product
                product.stock += item.quantity
                product.save()

            order.status = "cancelled"
            order.save()

        return Response({
            "success": True,
            "message": "Order cancelled successfully"
        }, status=status.HTTP_200_OK)


# -------------------------------
# ADMIN UPDATE ORDER STATUS
# -------------------------------

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        if not request.user.is_staff:
            return Response({
                "error": "Only admin can update order status"
            }, status=status.HTTP_403_FORBIDDEN)

        order = get_object_or_404(Order, id=id)

        new_status = request.data.get("status")

        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({
                "error": "Invalid status"
            }, status=status.HTTP_400_BAD_REQUEST)

        order.status = new_status
        order.save()

        return Response({
            "success": True,
            "message": "Status updated successfully"
        }, status=status.HTTP_200_OK)
    
# -------------------------------
# USER ADDRESS VIEWS
# -------------------------------
    
class AddressListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        addresses = Address.objects.filter(user=request.user).order_by("-created_at")
        serializer = AddressSerializer(addresses, many=True)
        return Response({"success": True, "addresses": serializer.data})

    def post(self, request):
        serializer = AddressSerializer(data=request.data)
        if serializer.is_valid():
            address = serializer.save(user=request.user)

            if address.is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)

            return Response({"success": True, "address": serializer.data}, status=201)

        return Response(serializer.errors, status=400)


class AddressDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, id):
        address = get_object_or_404(Address, id=id, user=request.user)
        serializer = AddressSerializer(address, data=request.data, partial=True)

        if serializer.is_valid():
            address = serializer.save()

            if address.is_default:
                Address.objects.filter(user=request.user).exclude(id=address.id).update(is_default=False)

            return Response({"success": True, "address": serializer.data})

        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        address = get_object_or_404(Address, id=id, user=request.user)
        address.delete()
        return Response({"success": True, "message": "Address deleted successfully"})