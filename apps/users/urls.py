from django.urls import path
from .views import *
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('signup/', SignupView.as_view()),
    path('login/', LoginView.as_view()),
    path('refresh/', TokenRefreshView.as_view()),
    path('profile/', ProfileView.as_view()),

    path('wishlist/', WishlistView.as_view()),
    path('wishlist/add/', AddToWishlistView.as_view()),
    path('wishlist/remove/<int:product_id>/', RemoveFromWishlistView.as_view()),
    path('assign-role/<int:user_id>/', AssignRoleView.as_view()),
]