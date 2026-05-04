from django.db import models
from apps.users.models import User
from apps.products.models import Product


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cart")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email}'s cart"


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    quantity = models.PositiveIntegerField(default=1)
    price_at_time = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ['cart', 'product']  # 🔥 prevents duplicate items

    def save(self, *args, **kwargs):
        # 🔥 Auto-set price when item is created
        if not self.price_at_time:
            self.price_at_time = self.product.price

        # 🔥 Quantity validation
        if self.quantity <= 0:
            raise ValueError("Quantity must be greater than 0")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"