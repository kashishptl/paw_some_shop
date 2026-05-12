from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import SignupView, LoginView, VerifyEmailView

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="login"),
    path("verify-email/<uidb64>/<token>/", VerifyEmailView.as_view(), name="verify-email"),
    path('refresh/', TokenRefreshView.as_view()),
    path('profile/', ProfileView.as_view()),

    path('wishlist/', WishlistView.as_view()),
    path('wishlist/add/', WishlistView.as_view(), name="wishlist-add"),
    path('wishlist/remove/<int:product_id>/', WishlistView.as_view(), name="wishlist-remove"),     
    path('deleteuser/<int:user_id>/', AssignRoleView.as_view()),
    path("dashboard/", UserDashboardView.as_view(), name="user-dashboard"),
]