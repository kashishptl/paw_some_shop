from django.urls import path
from .views import (
    CreateOrderView,
    OrderListView,
    OrderDetailView,
    CancelOrderView,
    UpdateOrderStatusView
)

urlpatterns = [
    path("create/", CreateOrderView.as_view()),
    path("", OrderListView.as_view()),
    path("<int:id>/", OrderDetailView.as_view()),
    path("<int:id>/cancel/", CancelOrderView.as_view()),
    path("<int:id>/status/", UpdateOrderStatusView.as_view()),
]   