from django.db.models import Count
from rest_framework import serializers

from categories import models


class NameSerializers(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class TitleSerializers(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    image = serializers.ImageField(required=False)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class FilteredListSerializer(serializers.ListSerializer):

    def to_representation(self, data):
        obj = self.context.get('obj', None)
        if obj:
            data = data.filter(sub_categories_product__design=obj.design,
                               sub_categories_product__design_type=obj.design_type)
        data = data.annotate(product_count=Count(
            'sub_categories_product')).filter(product_count__gt=1)
        return super(FilteredListSerializer, self).to_representation(data)


class SubCategoriesSerializers(serializers.ModelSerializer):
    product_count = serializers.IntegerField(required=False)

    class Meta:
        model = models.SubCategories
        # list_serializer_class = FilteredListSerializer
        fields = ("id", "title", "is_active", "image", "product_count")


class CategoriesSerializers(serializers.ModelSerializer):
    sub_categories = SubCategoriesSerializers(many=True)
    product_count = serializers.IntegerField(required=False)

    class Meta:
        model = models.Categories
        fields = ("id", "title", "is_active", "image",
                  "sub_categories", "product_count")


class CategoriesImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.CategoriesImage
        fields = ("id", "image",)


class SuperCategoriesSerializer(serializers.ModelSerializer):
    categories = CategoriesSerializers(many=True)

    class Meta:
        model = models.SuperCategories
        fields = ("id", "title", "is_active", "image", "categories")


class LimitSuperCategoriesSerializer(serializers.ModelSerializer):
    categories = CategoriesSerializers(many=True)

    class Meta:
        model = models.SuperCategories
        fields = ("id", "title", "is_active", "image", "categories")


class ChildSuperCategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.SuperCategories
        fields = ("id", "title", "is_active", "image")


class ChildCategoriesSerializers(serializers.ModelSerializer):
    super_category = ChildSuperCategoriesSerializer()
    category_images = CategoriesImageSerializer(many=True)

    class Meta:
        model = models.Categories
        fields = ("id", "title", "is_active", "image",
                  "super_category", "category_images")


class ChildSubCategoriesSerializers(serializers.ModelSerializer):
    category = ChildCategoriesSerializers()

    class Meta:
        model = models.SubCategories
        fields = ("id", "title", "is_active", "image", "category")


class ProductTagsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductTags
        fields = ("id", "title", "image",)


class CountriesSerializers(serializers.ModelSerializer):
    # Override image field to return the full URL for external images
    image = serializers.SerializerMethodField()

    class Meta:
        model = models.Countries
        fields = ("id", "title", "code", "code2", "dial_code", "shipping_fee", "redeem_point_cash",
                  "available_payment_gateway", "currency_type", "image", "cod_charge", "is_cod_available")

    def get_image(self, obj):
        # If image is a full URL (starts with http), return it as is
        if obj.image and str(obj.image).startswith('http'):
            return str(obj.image)
        # Otherwise, use the request to build the full URL
        request = self.context.get('request', None)
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        elif obj.image:
            return obj.image.url
        return None


class HomepageSectionProductSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField()
    country_prices = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    hover_image = serializers.SerializerMethodField()

    class Meta:
        model = models.HomepageSectionProduct
        fields = ("id", "product_id", "title", "subtitle", "image", "hover_image", "price", "original_price", "link_url",
                  "link_text", "rating", "reviews_count", "badge", "ordering", "is_active", "country_prices")

    def get_product_id(self, obj):
        # Return the actual product ID if it exists
        if obj.product:
            return obj.product.id
        # Fallback: try to locate product by title (case-insensitive contains)
        from product_management.models import Products
        try:
            product = Products.objects.filter(
                title__icontains=obj.title).first()
            if product:
                return product.id
        except Exception:
            pass
        return None

    def get_country_prices(self, obj):
        # Return country-specific pricing from the product
        if obj.product:
            prices = {}
            for pac in obj.product.product_country.all():
                prices[pac.country.code2] = {
                    'selling_price': pac.selling_price,
                    'original_price': pac.original_price,
                    'currency': pac.country.currency_type
                }
            return prices
        return {}

    def get_image(self, obj):
        # If section product has its own image, use it
        if obj.image:
            image_url = obj.image
            request = self.context.get('request', None)
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        # Otherwise, fallback to product's thumbnail_image
        product = obj.product
        if not product:
            # Try to find product by title (fallback for records without FK set)
            from product_management.models import Products
            try:
                product = Products.objects.filter(
                    title__icontains=obj.title).first()
            except Exception:
                pass
        if product and product.thumbnail_image:
            image_url = product.thumbnail_image.url
            request = self.context.get('request', None)
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        return None

    def get_hover_image(self, obj):
        product = obj.product
        if not product:
            from product_management.models import Products
            try:
                product = Products.objects.filter(
                    title__icontains=obj.title).first()
            except Exception:
                pass
        if product and hasattr(product, 'hover_image') and product.hover_image:
            image_url = product.hover_image.url
            request = self.context.get('request', None)
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        return None


class HomepageSectionSerializer(serializers.ModelSerializer):
    section_products = HomepageSectionProductSerializer(many=True)
    background_image = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()
    products_image = serializers.SerializerMethodField()
    promotion_slides = serializers.SerializerMethodField()

    class Meta:
        model = models.HomepageSection
        fields = ("id", "section_type", "title", "subtitle", "description", "image",
                  "background_image", "profile_image", "products_image",
                  "background_color", "link_url", "link_text", "ordering", "is_active",
                  "section_products", "promotion_slides")

    def _absolute_image_url(self, obj, field_name):
        field = getattr(obj, field_name)
        if not field:
            return None
        try:
            url = field.url
        except Exception:
            return None
        request = self.context.get('request', None)
        if request and not url.startswith('http'):
            return request.build_absolute_uri(url)
        return url

    def get_background_image(self, obj):
        return self._absolute_image_url(obj, 'background_image')

    def get_profile_image(self, obj):
        return self._absolute_image_url(obj, 'profile_image')

    def get_products_image(self, obj):
        return self._absolute_image_url(obj, 'products_image')

    def get_promotion_slides(self, obj):
        slides = obj.promotion_slides.filter(is_active=True).order_by('ordering')
        request = self.context.get('request', None)

        def abs_url(field):
            if not field:
                return None
            try:
                url = field.url
            except Exception:
                return None
            if request and not url.startswith('http'):
                return request.build_absolute_uri(url)
            return url

        return [{
            "id": s.id,
            "title": s.title,
            "subtitle": s.subtitle,
            "background_image": abs_url(s.background_image),
            "profile_image": abs_url(s.profile_image),
            "products_image": abs_url(s.products_image),
            "link_url": s.link_url,
            "link_text": s.link_text,
            "ordering": s.ordering,
            "is_active": s.is_active,
        } for s in slides]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Get the section products ordered by 'ordering' field
        section_products = instance.section_products.order_by('ordering').all()
        data['section_products'] = HomepageSectionProductSerializer(
            section_products, many=True, context=self.context).data
        return data


class HeroBannerProductSerializer(serializers.ModelSerializer):
    product_id = serializers.SerializerMethodField()
    country_prices = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = models.HeroBannerProduct
        fields = ("id", "product_id", "title", "subtitle", "image", "price", "original_price", "link_url",
                  "link_text", "rating", "reviews_count", "badge", "ordering", "is_active", "country_prices")

    def get_product_id(self, obj):
        if obj.product:
            return obj.product.id
        from product_management.models import Products
        try:
            product = Products.objects.filter(
                title__icontains=obj.title).first()
            if product:
                return product.id
        except Exception:
            pass
        return None

    def get_country_prices(self, obj):
        if obj.product:
            prices = {}
            for pac in obj.product.product_country.all():
                prices[pac.country.code2] = {
                    'selling_price': pac.selling_price,
                    'original_price': pac.original_price,
                    'currency': pac.country.currency_type
                }
            return prices
        return {}

    def get_image(self, obj):
        # If hero banner product has its own image, use it
        if obj.image:
            image_url = obj.image
            request = self.context.get('request', None)
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        # Otherwise, fallback to product's thumbnail_image
        product = obj.product
        if not product:
            # Try to find product by title (fallback for records without FK set)
            from product_management.models import Products
            try:
                product = Products.objects.filter(
                    title__icontains=obj.title).first()
            except Exception:
                pass
        if product and product.thumbnail_image:
            image_url = product.thumbnail_image.url
            request = self.context.get('request', None)
            if request and not image_url.startswith('http'):
                return request.build_absolute_uri(image_url)
            return image_url
        return None


class HeroBannerSerializer(serializers.ModelSerializer):
    video_url = serializers.SerializerMethodField()
    section_products = serializers.SerializerMethodField()

    class Meta:
        model = models.HeroBanner
        fields = ("id", "title", "video_url", "section",
                  "section_products", "ordering", "is_active")

    def get_video_url(self, obj):
        request = self.context.get('request')
        if obj.video:
            return request.build_absolute_uri(obj.video.url) if request else obj.video.url
        return None

    def get_section_products(self, obj):
        combined = []
        if obj.section:
            section_prods = obj.section.section_products.filter(
                is_active=True).order_by('ordering')
            combined.extend(HomepageSectionProductSerializer(
                section_prods, many=True, context=self.context).data)
        direct_prods = obj.banner_products.filter(
            is_active=True).order_by('ordering')
        combined.extend(HeroBannerProductSerializer(
            direct_prods, many=True, context=self.context).data)
        return combined
