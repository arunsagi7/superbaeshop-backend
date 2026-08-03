from django.core.validators import MinValueValidator
from django.db import models

from product_management.models import Products, Categories


class Coupon(models.Model):
    objects = None
    offer_code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=256)
    description = models.TextField()
    payout = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Offer Percentage")
    payout_details = models.TextField(blank=True, null=True)
    affiliate_process = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="offer_image", blank=True, null=True)
    video = models.FileField(upload_to="offer_video", blank=True, null=True)
    document = models.FileField(upload_to="offer_document", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)

    # updated_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tbl_coupons"
        verbose_name = "Coupon"
        verbose_name_plural = "Coupons"

    def __str__(self):
        return self.offer_code


OFFER_TYPE = (
    # (1, "Buy More & Save More "),
    (2, "Buy More & Get Free"),
    # (3, "Flat Offer %"),
    # (4, "Flat Offer Rs")
)


class Offers(models.Model):
    objects = None
    type = models.PositiveIntegerField(choices=OFFER_TYPE)
    title = models.CharField(max_length=120)
    categories = models.ManyToManyField(Categories, related_name="categories_offers", blank=True)
    products = models.ManyToManyField(Products, related_name="product_offers", blank=True)
    min_product = models.PositiveIntegerField(default=1)
    offer_value = models.PositiveIntegerField(default=0)
    max_discount = models.PositiveIntegerField(blank=True, null=True)
    short_descriptions = models.CharField(max_length=256)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_offers"
        verbose_name = "Product Offers"
        verbose_name_plural = "Offers"

    def __str__(self):
        return self.title


class OfferTerms(models.Model):
    objects = None
    offer = models.ForeignKey(Offers, on_delete=models.CASCADE, related_name="terms")
    title = models.CharField(max_length=256)
    icon = models.ImageField(blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_offer_terms"
        verbose_name = "Offer Term"
        verbose_name_plural = "Offer Terms"

    def __str__(self):
        return self.title
