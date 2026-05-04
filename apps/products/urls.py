from django.urls import path
from .views import (
    ProductListCreateView,
    ProductDetailView,
    ProductRateView,
    ProductRatingListView
)

urlpatterns = [

    # -------------------------------
    # PRODUCT APIs
    # -------------------------------

    # GET → all products
    # POST → create product (admin only)
    path('', ProductListCreateView.as_view(), name='product-list-create'),

    # GET → single product
    # PATCH → update product (admin only)
    # DELETE → delete product (admin only)
    path('<int:id>/', ProductDetailView.as_view(), name='product-detail'),


    # -------------------------------
    # RATING APIs
    # -------------------------------

    # POST → add/update rating (user)
    path('<int:id>/rate/', ProductRateView.as_view(), name='product-rate'),

    # GET → all ratings of a product
    path('<int:id>/ratings/', ProductRatingListView.as_view(), name='product-ratings'),
]