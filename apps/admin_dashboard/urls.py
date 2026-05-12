from django.urls import path
from .views import (
    AdminDashboardView,
    AdminPasswordSettingsView,
    AdminProductsView,
    AdminOrdersView,
    AdminProfileSettingsView,
    AdminStoreSettingsView,
    AdminUsersView,
    AdminCategoriesView,
    AdminReviewsView,
    AdminAnalyticsView,
)

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),

    path("products/", AdminProductsView.as_view(), name="admin-products"),
    path("orders/", AdminOrdersView.as_view(), name="admin-orders"),
    path("users/", AdminUsersView.as_view(), name="admin-users"),
    path("categories/", AdminCategoriesView.as_view(), name="admin-categories"),
    path("reviews/", AdminReviewsView.as_view(), name="admin-reviews"),
    path("analytics/", AdminAnalyticsView.as_view(), name="admin-analytics"),
    path("settings/profile/", AdminProfileSettingsView.as_view(), name="admin-profile-settings"),
    path("settings/password/", AdminPasswordSettingsView.as_view(), name="admin-password-settings"),
    path("settings/store/", AdminStoreSettingsView.as_view(), name="admin-store-settings"),
]