from django.db import models

from categories.validators import upload_to_title_images


class SuperCategories(models.Model):
    code = models.CharField(max_length=2)
    title = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)
    short_description = models.CharField(max_length=256, blank=True, null=True)
    image = models.ImageField(blank=True, null=True,
                              upload_to=upload_to_title_images)

    class Meta:
        db_table = "tbl_super_categories"
        verbose_name = "Super Category"
        verbose_name_plural = "Super Categories"

    def __str__(self):
        return self.title


class Categories(models.Model):
    super_category = models.ForeignKey(
        SuperCategories, on_delete=models.CASCADE, related_name="categories")
    code = models.CharField(max_length=3)
    title = models.CharField(max_length=220)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(blank=True, null=True,
                              upload_to=upload_to_title_images)

    class Meta:
        db_table = "tbl_categories"
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        unique_together = ("super_category", "title")

    def __str__(self):
        return self.title


class CategoriesImage(models.Model):
    category = models.ForeignKey(
        Categories, on_delete=models.CASCADE, related_name="category_images")
    image = models.ImageField(blank=True, null=True,
                              upload_to="category_images")

    class Meta:
        db_table = "tbl_categories_image"


class SubCategories(models.Model):
    code = models.CharField(max_length=3)
    category = models.ForeignKey(
        Categories, on_delete=models.CASCADE, related_name="sub_categories")
    title = models.CharField(max_length=220)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(blank=True, null=True,
                              upload_to=upload_to_title_images)

    class Meta:
        db_table = "tbl_sub_categories"
        verbose_name = "Sub Category"
        verbose_name_plural = "Sub Categories"
        unique_together = ("category", "title")

    def __str__(self):
        return "{}".format(self.title)


class PaymentGateWay(models.Model):
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_payment_gateway"
        verbose_name = "Payment Gateway"
        verbose_name_plural = "Payment Gateway"

    def __str__(self):
        return self.name


class Countries(models.Model):
    title = models.CharField(max_length=256)
    code = models.CharField(max_length=5, unique=True)
    code2 = models.CharField(max_length=2)
    dial_code = models.PositiveIntegerField()
    image = models.ImageField(upload_to="country_image")
    currency_type = models.CharField(
        max_length=5, verbose_name="Currency Symbol")
    shipping_fee = models.FloatField(
        help_text="Shipping charge free base amount")
    cod_charge = models.FloatField(
        help_text="Shipping charge free base amount")
    is_cod_available = models.BooleanField(default=True)
    redeem_point_cash = models.FloatField()
    available_payment_gateway = models.ManyToManyField(
        PaymentGateWay, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_countries"
        verbose_name = "Country"
        verbose_name_plural = "Country"

    def __str__(self):
        return self.title


class HomepageSection(models.Model):
    SECTION_TYPES = [
        ('hero', 'Hero Banner'),
        ('product_grid', 'Product Grid'),
        ('promotional_banner', 'Promotional Banner'),
        ('cute_collection', 'Cute Collection'),
        ('customers_top_choice', 'Customers Top Choice'),
        ('cute_collection_cards', 'Cute Collection Cards'),
        ('dream_box_collections', 'Dream Box Collections'),
        ('testimonials', 'Testimonials'),
        ('upgrade_essentials', 'Upgrade Essentials'),
        ('bestseller', 'Bestseller'),
        ('promotions_banner', 'Promotions Banner'),
    ]

    section_type = models.CharField(max_length=50, choices=SECTION_TYPES)
    title = models.CharField(max_length=255, blank=True, default='')
    subtitle = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    image = models.ImageField(upload_to='homepage/', blank=True, null=True)
    # Promotions Banner images
    background_image = models.ImageField(
        upload_to='homepage/promotions/', blank=True, null=True,
        help_text="Promotions Banner: animated/static background (webp)")
    profile_image = models.ImageField(
        upload_to='homepage/promotions/', blank=True, null=True,
        help_text="Promotions Banner: girl/person image")
    products_image = models.ImageField(
        upload_to='homepage/promotions/', blank=True, null=True,
        help_text="Promotions Banner: floating sticker products image")
    background_color = models.CharField(max_length=50, blank=True, default='')
    link_url = models.CharField(max_length=500, blank=True, default='')
    link_text = models.CharField(
        max_length=100, blank=True, default='Shop Now')
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_homepage_sections'
        verbose_name = 'Homepage Section'
        verbose_name_plural = 'Homepage Sections'
        ordering = ['ordering']

    def __str__(self):
        return f'{self.get_section_type_display()} - {self.title or "Untitled"}'


class PromotionSlide(models.Model):
    """Individual slide inside a Promotions Banner section (one section = many slides)."""
    section = models.ForeignKey(
        HomepageSection, on_delete=models.CASCADE, related_name='promotion_slides')
    title = models.CharField(max_length=255, blank=True, default='')
    subtitle = models.CharField(max_length=255, blank=True, default='')
    background_image = models.ImageField(
        upload_to='homepage/promotions/slides/', blank=True, null=True,
        help_text="Slide background (animated/static webp)")
    profile_image = models.ImageField(
        upload_to='homepage/promotions/slides/', blank=True, null=True,
        help_text="Girl/person image")
    products_image = models.ImageField(
        upload_to='homepage/promotions/slides/', blank=True, null=True,
        help_text="Floating sticker products image")
    link_url = models.CharField(max_length=500, blank=True, default='')
    link_text = models.CharField(max_length=100, blank=True, default='Shop Now')
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tbl_promotion_slides'
        verbose_name = 'Promotion Slide'
        verbose_name_plural = 'Promotion Slides'
        ordering = ['ordering']

    def __str__(self):
        return self.title or f'Slide {self.pk}'


class HomepageSectionProduct(models.Model):
    section = models.ForeignKey(
        HomepageSection, on_delete=models.CASCADE, related_name='section_products')
    product = models.ForeignKey('product_management.Products', on_delete=models.CASCADE,
                                blank=True, null=True, related_name='homepage_sections')
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default='')
    image = models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    link_url = models.CharField(max_length=500, blank=True, default='')
    link_text = models.CharField(max_length=100, blank=True, default='Buy Now')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    reviews_count = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=50, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_homepage_section_products'
        verbose_name = 'Homepage Section Product'
        verbose_name_plural = 'Homepage Section Products'
        ordering = ['ordering']

    def __str__(self):
        return f'{self.title}'


class PricingCategories(models.Model):
    title = models.CharField(max_length=120)
    from_start = models.PositiveIntegerField(verbose_name="Range From Price")
    to_end = models.PositiveIntegerField(verbose_name="Range To Price")
    code = models.CharField(max_length=3, unique=True)

    class Meta:
        db_table = "tbl_pricing_categories"
        verbose_name = "Pricing Categories"
        verbose_name_plural = "Pricing Categories"

    def __str__(self):
        return self.title


class ProductTags(models.Model):
    category = models.ForeignKey(
        Categories, on_delete=models.CASCADE, related_name="tags")
    title = models.CharField(max_length=120)
    image = models.ImageField(blank=True, null=True,
                              upload_to=upload_to_title_images)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tbl_category_product_tags"
        verbose_name = "Product & Category Tags"
        verbose_name_plural = "Product & Category Tags"

    def __str__(self):
        return "{} {}".format(self.category, self.title)


class ProductDesign(models.Model):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=120)

    class Meta:
        db_table = "tbl_product_design"
        verbose_name = "Product Design"
        verbose_name_plural = "Product Design"

    def __str__(self):
        return self.title


class DesignType(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=120, unique=True)
    image = models.ImageField(
        upload_to=upload_to_title_images, blank=True, null=True)

    class Meta:
        db_table = "tbl_design_type"
        verbose_name = "Design Type"
        verbose_name_plural = "Design Type"

    def __str__(self):
        return self.title


def upload_hero_banner_video(instance, filename):
    return f"hero_banners/videos/{filename}"


class HeroBanner(models.Model):
    title = models.CharField(
        max_length=255, help_text="Label for admin reference (e.g. Summer Sale Banner)")
    video = models.FileField(
        upload_to=upload_hero_banner_video, help_text="Upload .mp4 video file")
    section = models.ForeignKey(
        HomepageSection,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hero_banners",
        help_text="Link to a Homepage Section to show its products as cards when this banner plays"
    )
    ordering = models.PositiveIntegerField(
        default=0, help_text="Order in carousel (0 = first)")
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tbl_hero_banner"
        verbose_name = "Hero Banner"
        verbose_name_plural = "Hero Banners"
        ordering = ["ordering"]

    def __str__(self):
        return self.title


class HeroBannerProduct(models.Model):
    banner = models.ForeignKey(
        HeroBanner, on_delete=models.CASCADE, related_name='banner_products')
    product = models.ForeignKey(
        'product_management.Products', on_delete=models.CASCADE, blank=True, null=True)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True, default='')
    image = models.CharField(max_length=500, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    original_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True)
    link_url = models.CharField(max_length=500, blank=True, default='')
    link_text = models.CharField(max_length=100, blank=True, default='Buy Now')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.5)
    reviews_count = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=50, blank=True, default='')
    ordering = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tbl_hero_banner_products'
        verbose_name = 'Hero Banner Product'
        verbose_name_plural = 'Hero Banner Products'
        ordering = ['ordering']

    def __str__(self):
        return f'{self.title}'
