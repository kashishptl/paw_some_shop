from django.db import models
from apps.categories.models import Category
from django.conf import settings
from PIL import Image
import os

User = settings.AUTH_USER_MODEL

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField()
    image = models.ImageField(upload_to="products/")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # pehle file disk pe save ho jaye
        self._crop_image_to_square()

    def _crop_image_to_square(self):
        if not self.image:
            return
        img_path = self.image.path
        if not os.path.exists(img_path):
            return
        try:
            img = Image.open(img_path)

            # RGBA / palette → RGB convert karo (JPEG ke liye zaroori)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            w, h = img.size
            if w == h:
                return  # already square, kuch karne ki zaroorat nahi

            # Center se square crop
            side = min(w, h)
            left   = (w - side) // 2
            top    = (h - side) // 2
            right  = left + side
            bottom = top  + side
            img = img.crop((left, top, right, bottom))

            # 600×600 pe resize karo (bandwidth bachao)
            img = img.resize((600, 600), Image.LANCZOS)

            img.save(img_path, quality=90, optimize=True)
        except Exception:
            pass  # image corrupt ho toh silently skip

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
