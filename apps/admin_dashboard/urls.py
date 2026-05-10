from django.urls import path
from .views import (
    AdminDashboardView,
    AdminProductsView,
    AdminOrdersView,
    AdminUsersView,
    AdminCategoriesView,
    AdminReviewsView,
    AdminAnalyticsView,
    AdminSettingsView
)

urlpatterns = [
    path("", AdminDashboardView.as_view(), name="admin-dashboard"),

    path("products/", AdminProductsView.as_view(), name="admin-products"),
    path("orders/", AdminOrdersView.as_view(), name="admin-orders"),
    path("users/", AdminUsersView.as_view(), name="admin-users"),
    path("categories/", AdminCategoriesView.as_view(), name="admin-categories"),
    path("reviews/", AdminReviewsView.as_view(), name="admin-reviews"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("settings/", AdminSettingsView.as_view(), name="admin-settings"),
]