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
                "success": False,
                "message": "Cart is empty"
            }, status=status.HTTP_400_BAD_REQUEST)

        address_id = request.data.get("address_id")

        if not address_id:
            return Response({
                "success": False,
                "message": "address_id is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        address = get_object_or_404(Address, id=address_id, user=user)

        payment_method = request.data.get("payment_method", "cod")

        with transaction.atomic():

            subtotal = Decimal("0.00")

            # stock check first
            for item in cart_items:
                if item.quantity > item.product.stock:
                    return Response({
                        "success": False,
                        "message": f"Only {item.product.stock} items available for {item.product.name}"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # calculate subtotal
            for item in cart_items:
                subtotal += item.product.price * item.quantity

            tax = Decimal("0.00")
            shipping_charge = Decimal("0.00")
            total_amount = subtotal + tax + shipping_charge

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

                subtotal=subtotal,
                tax=tax,
                shipping_charge=shipping_charge,
                total_amount=total_amount,

                payment_method=payment_method
            )

            for item in cart_items:
                product = item.product

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=item.quantity,
                    price=product.price
                )

                product.stock -= item.quantity
                product.save()

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

        # admin can view any order
        if request.user.is_staff or request.user.role == "admin":
            order = get_object_or_404(Order, id=id)

        # customer can view only own order
        else:
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