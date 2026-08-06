import re

from django.core.validators import MaxValueValidator
from django.db import models
from django.utils.safestring import mark_safe

from categories.models import SubCategories, Countries, PricingCategories, Categories, ProductTags, ProductDesign, \
    DesignType
from product_management.validators import upload_to_title_images

CONTENT_CHOICE = (
    ("Return Policy", "Return Policy"),
    ("Terms and Conditions", "Terms and Conditions"),
    ("Damage and exchange", "Damage and exchange"),
    ("Note", "Note"),
    ("Delivery Details", "Delivery Details"),
)

PRODUCT_STATUS_CHOICE = (
    (1, "Uploaded"),
    (2, "Need to Content"),
    (3, "Content Updated"),
    (4, "Approved"),
    (5, "Published"),
)


def year_code_generate(year):
    my_dict = {1: 'A', 2: 'B', 3: 'C', 4: 'D', 5: 'E',
               6: 'F', 7: 'G', 8: 'H', 9: 'J', 0: 'K'}
    result = ""
    for number in str(year)[2:]:
        result += my_dict[int(number)]
    return result


class Products(models.Model):
    sku = models.CharField(max_length=60, unique=True)
    title = models.CharField(max_length=256)
    slug = models.SlugField()
    bt_code = models.CharField(max_length=30, blank=True, null=True)
    short_descriptions = models.CharField(
        max_length=256, blank=True, null=True)
    category = models.ForeignKey(
        Categories, on_delete=models.CASCADE, related_name="product_categories")
    sub_category = models.ForeignKey(
        SubCategories, on_delete=models.CASCADE, blank=True, null=True, related_name="sub_categories_product")
    thumbnail_image = models.ImageField(upload_to=upload_to_title_images)
    hover_image = models.ImageField(upload_to=upload_to_title_images, blank=True, null=True)
    support_number = models.CharField(max_length=15)
    stock_qty = models.PositiveIntegerField()
    tags = models.ManyToManyField(ProductTags, blank=True)
    weight = models.FloatField()
    design_type = models.ForeignKey(DesignType, blank=True, null=True, related_name="product_designs_type",
                                    on_delete=models.CASCADE)
    design = models.ForeignKey(ProductDesign, blank=True, null=True, related_name="product_designs",
                               on_delete=models.CASCADE)

    financial_year = models.CharField(max_length=4, blank=True, null=True)
    price_category = models.ForeignKey(
        PricingCategories, on_delete=models.CASCADE, blank=True, null=True)

    affiliate_percentage = models.PositiveIntegerField(
        validators=[MaxValueValidator(80)], default=5)
    is_pre_order = models.BooleanField(default=False)
    is_barter = models.BooleanField(default=False)
    is_barter_order_count = models.PositiveIntegerField(
        validators=[MaxValueValidator(5)], default=5)
    # is_hero_featured field removed

    status = models.IntegerField(choices=PRODUCT_STATUS_CHOICE, default=1)
    ordering = models.PositiveIntegerField(default=0)
    is_stock = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_products"
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-ordering']

    def __str__(self):
        return self.sku

    def stock_status(self):
        if self.stock_qty > 0:
            self.is_stock = True
            self.save()
            return True
        self.is_stock = False
        self.save()
        return False

    def image_tag(self):
        if self.thumbnail_image:
            image_url = self.thumbnail_image.url
            return mark_safe(
                f"<img src='{image_url}' width='150' height='150' style='object-fit: cover' />")
        # Try first product image as fallback
        first_image = self.product_images.first()
        if first_image and first_image.image:
            image_url = first_image.image.url
            return mark_safe(
                f"<img src='{image_url}' width='150' height='150' style='object-fit: cover' />")
        return mark_safe("<span style='color: #999'>No Image</span>")


class ProductImages(models.Model):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="product_images")
    title = models.CharField(max_length=120)
    image = models.ImageField(upload_to="product/product-image/")

    class Meta:
        db_table = "tbl_product_image"
        verbose_name = "Product Image"
        verbose_name_plural = "Product Images"


class ProductVideos(models.Model):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="product_videos")
    title = models.CharField(max_length=120)
    video = models.FileField(upload_to=upload_to_title_images)
    content_type = models.CharField(max_length=120)

    class Meta:
        db_table = "tbl_product_videos"
        verbose_name = "Product Video"
        verbose_name_plural = "Product Videos"


class ProductAvailableCountries(models.Model):
    country = models.ForeignKey(Countries, on_delete=models.CASCADE)
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="product_country")
    original_price = models.PositiveIntegerField()
    selling_price = models.PositiveIntegerField()
    promotion_text = models.CharField(max_length=256, blank=True, null=True)

    class Meta:
        db_table = "tbl_product_available_countries"
        verbose_name = "Product Available Country"
        verbose_name_plural = "Product Available Countries"
        unique_together = ("product", "country")


class ProductContent(models.Model):
    product = models.ForeignKey(
        Products, on_delete=models.CASCADE, related_name="product_content")
    heading = models.CharField(max_length=256)
    content = models.TextField()

    class Meta:
        db_table = "tbl_product_content"
        verbose_name = "Product Content"
        verbose_name_plural = "Product Content"
        unique_together = ("product", "heading")
