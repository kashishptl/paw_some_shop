from django.urls import path

from .views import (
    CreateRazorpayOrderView,
    VerifyRazorpayPaymentView,
    CashOnDeliveryView,
    MyPaymentsView,
    AdminPaymentListView,
    CancelPaymentView,
    UpdatePaymentMethodView,
    UpdatePaymentStatusView,
)

urlpatterns = [

    # =========================================
    # RAZORPAY PAYMENT APIs
    # =========================================

    # Create Razorpay Order
    path("razorpay/create/",CreateRazorpayOrderView.as_view(),name="create-razorpay-order"),

    # Verify Razorpay Payment
    path("razorpay/verify/",VerifyRazorpayPaymentView.as_view(),name="verify-razorpay-payment"),


    # =========================================
    # CASH ON DELIVERY APIs
    # =========================================

    # Select COD Payment Method
    path("cod/",CashOnDeliveryView.as_view(),name="cash-on-delivery"),


    # =========================================
    # USER PAYMENT APIs
    # =========================================

    # Get Logged-in User Payments
    path("my-payments/",MyPaymentsView.as_view(),name="my-payments"),

    # Cancel Payment
    path("<int:payment_id>/cancel/",CancelPaymentView.as_view(),name="cancel-payment"),

    # Change Payment Method
    path("<int:payment_id>/update-method/",UpdatePaymentMethodView.as_view(),name="update-payment-method"),


    # =========================================
    # ADMIN PAYMENT APIs
    # =========================================

    # Get All Payments
    path("admin/all/",AdminPaymentListView.as_view(),name="admin-payments"),

    # Update Payment Status
    path("admin/<int:payment_id>/update-status/",UpdatePaymentStatusView.as_view(),name="update-payment-status"),
]