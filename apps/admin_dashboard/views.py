from django.db.models import Sum, Count, Avg, F
from django.db.models.functions import TruncMonth, TruncDay
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from datetime import timedelta
from django.utils import timezone

from apps.users.models import User
from apps.products.models import Product, Rating
from apps.categories.models import Category
from apps.orders.models import Order
from apps.users.permissions import IsManagerOrAdmin
from .models import SiteSettings

# ==============================
# ADMIN DASHBOARD
# ==============================
class AdminDashboardView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_sales = Order.objects.exclude(status="cancelled").aggregate(
            total=Sum("total_amount")
        )["total"] or 0

        total_orders = Order.objects.count()
        total_users = User.objects.count()
        total_products = Product.objects.count()

        recent_orders = Order.objects.select_related("user").order_by("-created_at")[:6]

        recent_orders_data = []
        for order in recent_orders:
            recent_orders_data.append({
                "order_id": f"PWS-{order.id}",
                "customer": order.user.name,
                "email": order.user.email,
                "date": order.created_at,
                "status": order.status,
                "payment": getattr(order, "payment_status", "paid"),
                "amount": order.total_amount,
            })

        top_products = Product.objects.annotate(
            review_count=Count("ratings"),
            avg_rating=Avg("ratings__rating")
        ).order_by("-review_count")[:5]

        top_products_data = []
        for product in top_products:
            top_products_data.append({
                "id": product.id,
                "name": product.name,
                "brand": getattr(product, "brand", ""),
                "price": product.price,
                "image": product.image.url if product.image else None,
                "reviews": product.review_count,
                "rating": round(product.avg_rating or 0, 1),
            })

        return Response({
            "success": True,
            "message": "Dashboard data fetched successfully",
            "data": {
                "cards": {
                    "total_sales": total_sales,
                    "total_orders": total_orders,
                    "total_users": total_users,
                    "total_products": total_products,
                },
                "recent_orders": recent_orders_data,
                "top_products": top_products_data,
            }
        })


# ==============================
# ADMIN PRODUCTS PAGE
# ==============================
class AdminProductsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        products = Product.objects.select_related("category").annotate(
            avg_rating=Avg("ratings__rating")
        ).order_by("-created_at")

        data = []
        for product in products:
            data.append({
                "id": product.id,
                "name": product.name,
                "brand": getattr(product, "brand", ""),
                "category": product.category.name if product.category else None,
                "price": product.price,
                "stock": product.stock,
                "rating": round(product.avg_rating or 0, 1),
                "image": product.image.url if product.image else None,
                "is_active": product.is_active,
            })

        return Response({
            "success": True,
            "count": products.count(),
            "data": data
        })


# ==============================
# ADMIN ORDERS PAGE
# ==============================
class AdminOrdersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        orders = Order.objects.select_related("user").order_by("-created_at")

        data = []
        for order in orders:
            data.append({
                "id": order.id,
                "order_id": f"PWS-{order.id}",
                "customer": order.user.name,
                "email": order.user.email,
                "date": order.created_at,
                "status": order.status,
                "payment": getattr(order, "payment_status", "paid"),
                "amount": order.total_amount,
            })

        return Response({
            "success": True,
            "count": orders.count(),
            "data": data
        })


# ==============================
# ADMIN USERS PAGE
# ==============================
class AdminUsersView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.annotate(
            order_count=Count("orders"),
            total_spent=Sum("orders__total_amount")
        ).order_by("-id")

        data = []
        for user in users:
            data.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
                "joined": user.created_at if hasattr(user, "created_at") else None,
                "orders": user.order_count,
                "spent": user.total_spent or 0,
                "status": "Active" if user.is_active else "Blocked",
            })

        return Response({
            "success": True,
            "count": users.count(),
            "data": data
        })


# ==============================
# ADMIN CATEGORIES PAGE
# ==============================
class AdminCategoriesView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        categories = Category.objects.annotate(
            product_count=Count("products")
        )

        data = []
        for category in categories:
            data.append({
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "products": category.product_count,
                "is_active": category.is_active,
                "image": category.image.url if category.image else None,
            })

        return Response({
            "success": True,
            "count": categories.count(),
            "data": data
        })


# ==============================
# ADMIN REVIEWS PAGE
# ==============================
class AdminReviewsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        reviews = Rating.objects.select_related("product", "user").order_by("-created_at")

        data = []
        for review in reviews:
            data.append({
                "id": review.id,
                "product": review.product.name,
                "user": review.user.name,
                "rating": review.rating,
                "comment": review.review,
                "status": getattr(review, "status", "approved"),
                "created_at": review.created_at,
            })

        return Response({
            "success": True,
            "count": reviews.count(),
            "data": data
        })


# ==============================
# ADMIN ANALYTICS PAGE
# ==============================
class AdminAnalyticsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        last_30_days = today - timedelta(days=30)

        # Daily revenue - last 30 days
        daily_revenue_qs = Order.objects.filter(
            created_at__date__gte=last_30_days
        ).exclude(
            status="cancelled"
        ).annotate(
            day=TruncDay("created_at")
        ).values("day").annotate(
            revenue=Sum("total_amount")
        ).order_by("day")

        daily_revenue = []
        for item in daily_revenue_qs:
            daily_revenue.append({
                "day": item["day"].date() if item["day"] else None,
                "revenue": item["revenue"] or 0
            })

        # Monthly orders
        monthly_orders_qs = Order.objects.annotate(
            month=TruncMonth("created_at")
        ).values("month").annotate(
            orders=Count("id")
        ).order_by("month")

        monthly_orders = []
        for item in monthly_orders_qs:
            monthly_orders.append({
                "month": item["month"].strftime("%B %Y") if item["month"] else None,
                "orders": item["orders"]
            })

        # Category product count
            category_share_qs = Category.objects.annotate(
            product_count=Count("products")
        ).values("name", "product_count")

        category_share = []

        for item in category_share_qs:
            category_share.append({
                "name": item["name"],
                "products": item["product_count"]
            })

        return Response({
            "success": True,
            "data": {
                "daily_revenue": daily_revenue,
                "monthly_orders": monthly_orders,
                "category_share": category_share,
            }
        })
    
# ==============================
# ADMIN SETTINGS PAGE
# ==============================
# apps/admin_dashboard/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import SiteSettings


class AdminProfileSettingsView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        user = request.user
        return Response({
            "success": True,
            "data": {
                "name": user.name,
                "email": user.email,
            }
        })

    def patch(self, request):
        user = request.user

        user.name = request.data.get("name", user.name)
        user.email = request.data.get("email", user.email)
        user.save()

        return Response({
            "success": True,
            "message": "Profile updated successfully",
            "data": {
                "name": user.name,
                "email": user.email,
            }
        })


class AdminPasswordSettingsView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def patch(self, request):
        user = request.user

        current_password = request.data.get("current_password")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if not current_password or not new_password or not confirm_password:
            return Response({
                "success": False,
                "message": "All password fields are required"
            }, status=400)

        if not user.check_password(current_password):
            return Response({
                "success": False,
                "message": "Current password is incorrect"
            }, status=400)

        if new_password != confirm_password:
            return Response({
                "success": False,
                "message": "New password and confirm password do not match"
            }, status=400)

        try:
            validate_password(new_password, user)
        except ValidationError as e:
            return Response({
                "success": False,
                "message": e.messages
            }, status=400)

        user.set_password(new_password)
        user.save()

        return Response({
            "success": True,
            "message": "Password updated successfully"
        })


class AdminStoreSettingsView(APIView):
    permission_classes = [IsManagerOrAdmin]

    def get(self, request):
        settings = SiteSettings.objects.first()

        if not settings:
            settings = SiteSettings.objects.create(
                site_name="Pawsome",
                support_email="support@pawsome.com",
                currency="INR",
                tax_percentage=0,
                shipping_charge=0,
                maintenance_mode=False
            )

        return Response({
            "success": True,
            "data": {
                "site_name": settings.site_name,
                "support_email": settings.support_email,
                "currency": settings.currency,
                "tax_percentage": settings.tax_percentage,
                "shipping_charge": settings.shipping_charge,
                "maintenance_mode": settings.maintenance_mode,
                "logo": settings.logo.url if settings.logo else None,
            }
        })

    def patch(self, request):
        settings = SiteSettings.objects.first()

        if not settings:
            settings = SiteSettings.objects.create()

        settings.site_name = request.data.get("site_name", settings.site_name)
        settings.support_email = request.data.get("support_email", settings.support_email)
        settings.currency = request.data.get("currency", settings.currency)
        settings.tax_percentage = request.data.get("tax_percentage", settings.tax_percentage)
        settings.shipping_charge = request.data.get("shipping_charge", settings.shipping_charge)
        settings.maintenance_mode = request.data.get("maintenance_mode", settings.maintenance_mode)

        if request.FILES.get("logo"):
            settings.logo = request.FILES.get("logo")

        settings.save()

        return Response({
            "success": True,
            "message": "Store settings updated successfully",
            "data": {
                "site_name": settings.site_name,
                "support_email": settings.support_email,
                "currency": settings.currency,
                "tax_percentage": settings.tax_percentage,
                "shipping_charge": settings.shipping_charge,
                "maintenance_mode": settings.maintenance_mode,
                "logo": settings.logo.url if settings.logo else None,
            }
        })