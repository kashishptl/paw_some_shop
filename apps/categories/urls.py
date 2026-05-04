from django.urls import path
from .views import (
    CategoryListCreateView,
    CategoryDetailView,
    CategoryProductsView
)

urlpatterns = [

    # -------------------------------
    # Category APIs
    # -------------------------------

    path('', CategoryListCreateView.as_view(), name='category-list-create'),
    # GET  -> all categories (user + admin)
    # POST -> create category (admin only)


    path('<int:id>/', CategoryDetailView.as_view(), name='category-detail'),
    # PATCH  -> update category (admin only)
    # DELETE -> delete category (admin only)


    path('<slug:slug>/products/', CategoryProductsView.as_view(), name='category-products'),
    # GET -> all products of specific category

]