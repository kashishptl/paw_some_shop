from django.urls import path
from .views import (
    AddressDetailView,
    AddressListCreateView,
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
    path("addresses/", AddressListCreateView.as_view(), name="address-list-create"),
    path("addresses/<int:id>/", AddressDetailView.as_view(), name="address-detail"),
]   