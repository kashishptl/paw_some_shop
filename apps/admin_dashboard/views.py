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
                "joined": user.date_joined if hasattr(user, "date_joined") else None,
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
class AdminSettingsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        settings = SiteSettings.objects.first()

        if not settings:
            return Response({
                "success": False,
                "message": "Settings not found"
            })

        data = {
            "site_name": settings.site_name,
            "support_email": settings.support_email,
            "currency": settings.currency,
            "tax_percentage": settings.tax_percentage,
            "shipping_charge": settings.shipping_charge,
            "maintenance_mode": settings.maintenance_mode,
            "logo": settings.logo.url if settings.logo else None,
        }

        return Response({
            "success": True,
            "data": data
        })