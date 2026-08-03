from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from accounts.models import UserProfile
from product_management.models import Products


class Cart(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="my_cart")
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MaxValueValidator(9)])
    is_offer = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    color_code = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = "tbl_cart"
        verbose_name = "Cart"
        verbose_name_plural = "Cart"
        unique_together = ("user", "product")

    def product_price(self):
        country = self.product.product_country.filter(country=self.user.country).first()
        if country:
            return {"original_price": country.original_price, "selling_price": country.selling_price,
                    "currency_type": country.country.currency_type}
        return {"original_price": 0, "selling_price": 0, "currency_type": "₹"}


class GuestCart(models.Model):
    session_id = models.CharField(max_length=255)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MaxValueValidator(9)])
    is_offer = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    color_code = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = "tbl_guest_cart"
        verbose_name = "Guest Cart"
        verbose_name_plural = "Guest Cart"
        unique_together = ("session_id", "product")

    def product_price(self):
        # Fallback to INR pricing for guests, or we could pass country in session headers if needed.
        # Products serialize with 'product_country' array, so this matches Cart behavior.
        country = self.product.product_country.first()
        if country:
            return {"original_price": country.original_price, "selling_price": country.selling_price,
                    "currency_type": country.country.currency_type}
        return {"original_price": 0, "selling_price": 0, "currency_type": "₹"}