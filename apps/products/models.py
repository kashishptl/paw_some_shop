from django.db import models
from apps.categories.models import Category
from django.conf import settings

User = settings.AUTH_USER_MODEL


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to="products/")

    # brand = models.CharField(max_length=100, blank=True, null=True)
    

    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_average_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            return round(sum(r.rating for r in ratings) / ratings.count(), 1)
        return 0


class Rating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="ratings")
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    rating = models.IntegerField()  # 1–5
    review = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')

    def __str__(self):
        return f"{self.product.name} - {self.rating}"