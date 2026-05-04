from django.urls import path
from .views import (
    CartView,
    AddToCartView,
    UpdateCartView,
    RemoveFromCartView,
    ClearCartView
)

urlpatterns = [

    # -------------------------------
    # 🛒 Cart APIs
    # -------------------------------

    path('', CartView.as_view(), name='cart'),                         # GET → view cart

    path('add/', AddToCartView.as_view(), name='add-to-cart'),        # POST → add product

    path('update/', UpdateCartView.as_view(), name='update-cart'),    # PATCH → update quantity

    path('remove/<int:product_id>/', RemoveFromCartView.as_view(), name='remove-from-cart'),  # DELETE → remove item

    path('clear/', ClearCartView.as_view(), name='clear-cart'),       # DELETE → clear cart
]