import razorpay

from django.conf import settings
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from apps.orders.models import Order
from .models import Payment
from .serializers import PaymentSerializer


# ==============================
# CREATE RAZORPAY ORDER
# ==============================
class CreateRazorpayOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({
                "success": False,
                "message": "order_id is required"
            }, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        # Check cancelled order
        if order.status == "cancelled":
            return Response({
                "success": False,
                "message": "Cancelled order cannot be paid"
            }, status=400)

        # Check already paid
        if Payment.objects.filter(order=order, status="success").exists():
            return Response({
                "success": False,
                "message": "This order is already paid"
            }, status=400)

        # Check pending payment already created
        existing_pending_payment = Payment.objects.filter(
            order=order,
            user=request.user,
            status="pending"
        ).first()

        if existing_pending_payment:
            return Response({
                "success": False,
                "message": "Payment already initiated for this order"
            }, status=400)

        # Product stock check
        for item in order.items.all():
            if item.quantity > item.product.stock:
                return Response({
                    "success": False,
                    "message": f"{item.product.name} is out of stock"
                }, status=400)

        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        amount_in_paise = int(order.total_amount * 100)

        razorpay_order = client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1
        })

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=order.total_amount,
            payment_method="upi",
            status="pending",
            razorpay_order_id=razorpay_order["id"],
            transaction_id=None
        )

        return Response({
            "success": True,
            "message": "Razorpay order created successfully",
            "data": {
                "payment_db_id": payment.id,

                "order_id": order.id,

                "order_status": order.status,

                "razorpay_order_id": razorpay_order["id"],

                "razorpay_key": settings.RAZORPAY_KEY_ID,

                "amount": amount_in_paise,

                "currency": "INR",

                "payment_method": payment.payment_method,

                "customer": {
                    "name": request.user.name,
                    "email": request.user.email,
                }
            }
        }, status=201)
            



# ==============================
# VERIFY RAZORPAY PAYMENT
# ==============================
class VerifyRazorpayPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        razorpay_order_id = request.data.get("razorpay_order_id")
        razorpay_payment_id = request.data.get("razorpay_payment_id")
        razorpay_signature = request.data.get("razorpay_signature")

        if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
            return Response({
                "success": False,
                "message": "razorpay_order_id, razorpay_payment_id and razorpay_signature are required"
            }, status=400)

        client = razorpay.Client(auth=(
            settings.RAZORPAY_KEY_ID,
            settings.RAZORPAY_KEY_SECRET
        ))

        try:
            client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })

            payment = get_object_or_404(
                Payment,
razorpay_order_id=razorpay_order_id,
user=request.user
            )

            payment.status = "success"
            payment.transaction_id = razorpay_payment_id
            payment.save()

            serializer = PaymentSerializer(payment)

            return Response({
                "success": True,
                "message": "Payment verified successfully",
                "data": serializer.data
            })

        except Exception:
            payment = Payment.objects.filter(
                razorpay_order_id=razorpay_order_id,
                user=request.user
            ).first()

            if payment:
                payment.status = "failed"
                payment.save()

            return Response({
                "success": False,
                "message": "Payment verification failed"
            }, status=400)


# ==============================
# CASH ON DELIVERY
# ==============================
class CashOnDeliveryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        order_id = request.data.get("order_id")

        if not order_id:
            return Response({
                "success": False,
                "message": "order_id is required"
            }, status=400)

        order = get_object_or_404(Order, id=order_id, user=request.user)

        payment = Payment.objects.create(
            order=order,
            user=request.user,
            amount=order.total_amount,
            payment_method="cod",
            status="pending"
        )

        serializer = PaymentSerializer(payment)

        return Response({
            "success": True,
            "message": "Cash on Delivery selected successfully",
            "data": serializer.data
        }, status=201)


# ==============================
# MY PAYMENTS
# ==============================
class MyPaymentsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payments = Payment.objects.filter(user=request.user).order_by("-created_at")
        serializer = PaymentSerializer(payments, many=True)

        return Response({
            "success": True,
            "count": payments.count(),
            "data": serializer.data
        })


# ==============================
# ADMIN ALL PAYMENTS
# ==============================
class AdminPaymentListView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        payments = Payment.objects.all().order_by("-created_at")
        serializer = PaymentSerializer(payments, many=True)

        return Response({
            "success": True,
            "count": payments.count(),
            "data": serializer.data
        })

# ==============================
# CANCEL PAYMENT
# ==============================

class CancelPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, payment_id):

        payment = get_object_or_404(
            Payment,
            id=payment_id,
            user=request.user
        )

        if payment.status == "success":
            return Response({
                "success": False,
                "message": "Successful payment cannot be cancelled"
            }, status=400)

        payment.status = "failed"
        payment.save()

        serializer = PaymentSerializer(payment)

        return Response({
            "success": True,
            "message": "Payment cancelled successfully",
            "data": serializer.data
        })

# ==============================
# UPDATE PAYMENT METHOD
# ==============================

class UpdatePaymentMethodView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, payment_id):

        payment = get_object_or_404(
            Payment,
            id=payment_id,
            user=request.user
        )

        new_method = request.data.get("payment_method")

        if new_method not in ["cod", "upi", "card"]:
            return Response({
                "success": False,
                "message": "Invalid payment method"
            }, status=400)

        if payment.status == "success":
            return Response({
                "success": False,
                "message": "Cannot change successful payment method"
            }, status=400)

        payment.payment_method = new_method
        payment.save()

        serializer = PaymentSerializer(payment)

        return Response({
            "success": True,
            "message": "Payment method updated successfully",
            "data": serializer.data
        })


# ==============================
# UPDATE PAYMENT STATUS Admin Only
# ==============================
    
class UpdatePaymentStatusView(APIView):
    permission_classes = [IsAdminUser]

    def patch(self, request, payment_id):

        payment = get_object_or_404(Payment, id=payment_id)

        new_status = request.data.get("status")

        if new_status not in ["pending", "success", "failed"]:
            return Response({
                "success": False,
                "message": "Invalid payment status"
            }, status=400)

        payment.status = new_status
        payment.save()

        serializer = PaymentSerializer(payment)

        return Response({
            "success": True,
            "message": "Payment status updated successfully",
            "data": serializer.data
        })