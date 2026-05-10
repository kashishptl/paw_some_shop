from django.db import models


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=200)
    support_email = models.EmailField()

    currency = models.CharField(max_length=10, default="INR")

    tax_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    shipping_charge = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    maintenance_mode = models.BooleanField(default=False)

    logo = models.ImageField(
        upload_to="settings/",
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.site_name