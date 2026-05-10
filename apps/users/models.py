from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from apps.products.models import Product


# =========================
# USER MANAGER
# =========================
class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(email, name, password, **extra_fields)


# =========================
# CUSTOM USER MODEL
# =========================
class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("manager", "Manager"),
        ("customer", "Customer"),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="customer")

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    

    created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email


# =========================
# WISHLIST MODEL
# =========================
class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.email} - {self.product}"