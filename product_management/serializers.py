from annoying.functions import get_object_or_None
from django.db.models import Sum, Count
from rest_framework import serializers

from cart_management.models import Cart
from categories.models import SuperCategories
from categories.serializers import CountriesSerializers, SuperCategoriesSerializer, CategoriesSerializers, \
    ChildCategoriesSerializers
from offers_management.serializers import OfferSerializers
from orders_management.models import InfluencerOrder
from . import models


class TitleSerializer(serializers.Serializer):
    id = serializers.CharField()
    title = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ProductContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.ProductContent
        fields = ("id", "heading", "content")


class ProductAvailableCountriesSerializer(serializers.ModelSerializer):
    country = CountriesSerializers()

    class Meta:
        model = models.ProductAvailableCountries
        fields = ("id", "country", "product", "original_price",
                  "selling_price", "promotion_text")


class ProductVideosSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.ProductVideos
        fields = ("id", "title", "video", "content_type")


class ProductImagesSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.ProductImages
        fields = ("id", "title", "image")


class SubcategorySerializer(serializers.ModelSerializer):
    category = TitleSerializer()

    class Meta:
        model = models.SubCategories
        fields = ("id", "category", "title", "image")


class ListProductSerializers(serializers.ModelSerializer):
    sub_category = SubcategorySerializer()
    category = ChildCategoriesSerializers()

    product_country = ProductAvailableCountriesSerializer(many=True)
    product_offers = OfferSerializers(many=True)

    in_cart = serializers.SerializerMethodField()
    thumbnail_image = serializers.SerializerMethodField()
    product_images = ProductImagesSerializers(many=True, read_only=True)

    class Meta:
        model = models.Products
        fields = ("id", "sku", "title", "slug", "sub_category", "thumbnail_image", "product_country",
                  "short_descriptions", "product_offers", "in_cart", "stock_status", "is_pre_order", "category", "product_images")

    def get_in_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            if hasattr(user, "userprofile"):
                cart = get_object_or_None(
                    Cart, product=obj, user=user.userprofile)
                if cart:
                    return {"id": cart.id, "quantity": cart.quantity, }
        return None

    def get_thumbnail_image(self, obj):
        request = self.context.get('request')

        # First try to get the first product image from product_images
        try:
            first_product_image = models.ProductImages.objects.filter(
                product=obj).first()
            if first_product_image and first_product_image.image:
                image_url = first_product_image.image.url if hasattr(
                    first_product_image.image, 'url') else first_product_image.image
                if request:
                    return request.build_absolute_uri(image_url)
                return image_url
        except Exception:
            pass

        # If no product_images, try thumbnail_image
        if obj.thumbnail_image:
            image_url = obj.thumbnail_image.url if hasattr(
                obj.thumbnail_image, 'url') else obj.thumbnail_image
            if request:
                return request.build_absolute_uri(image_url)
            return image_url

        # Return None - frontend will handle placeholder
        return None


class ProductsSerializers(serializers.ModelSerializer):
    product_images = ProductImagesSerializers(many=True)
    product_videos = ProductVideosSerializers(many=True)
    product_country = ProductAvailableCountriesSerializer(many=True)
    product_content = ProductContentSerializer(many=True)
    product_offers = OfferSerializers(many=True)

    sub_category = SubcategorySerializer()
    in_cart = serializers.SerializerMethodField()
    barter_order = serializers.SerializerMethodField()
    barter_order_count = serializers.SerializerMethodField()
    sub_product = serializers.SerializerMethodField()
    category = ChildCategoriesSerializers(read_only=True)

    # other_models = serializers.SerializerMethodField()

    class Meta:
        model = models.Products
        fields = ("id", "sku", "title", "slug", "sub_category", "thumbnail_image", "support_number", "is_barter",
                  "is_pre_order", "is_active", "created_on", "product_images", "product_videos", "product_country",
                  "product_content", "is_barter_order_count", "affiliate_percentage", "in_cart", "barter_order",
                  "barter_order_count", "short_descriptions", "stock_status", "product_offers", "sub_product",
                  "category")

    def get_in_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            if hasattr(user, "userprofile"):
                cart = get_object_or_None(
                    Cart, product=obj, user=user.userprofile)
                if cart:
                    return {"id": cart.id, "quantity": cart.quantity, }
        return None

    def get_sub_product(self, obj):
        request = self.context['request']
        if obj.id in [2]:
            product = models.Products.objects.get(id=1)
            return ProductsSerializers(product, context={"request": request}).data
        return None

    # def get_other_models(self, obj):
    #     obj_type = models.Categories.objects.filter(product_categories__design=obj.design,
    #                                                 product_categories__design_type=obj.design_type)
    #     return CategoriesSerializers(obj_type, many=True,
    #                                  context={"request": self.context['request'], "obj": obj}).data

    def get_barter_order(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            if hasattr(user, "affiliates"):
                cart = get_object_or_None(
                    InfluencerOrder, product=obj, affiliates=user.affiliates)
                if cart:
                    return {"id": cart.id}
                quantity = obj.product_order.filter(order__is_success=True, order__coupon=user.affiliates.offer
                                                    ).aggregate(quantity=Sum('quantity'))['quantity']
                if quantity is None:
                    quantity = 0
                if quantity >= obj.is_barter_order_count:
                    return True
            return False

    def get_barter_order_count(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            if hasattr(user, "affiliates"):
                quantity = obj.product_order.filter(order__is_success=True, order__coupon=user.affiliates.offer
                                                    ).aggregate(quantity=Sum('quantity'))['quantity']
                return quantity

        return None


class UploadProductSerializer(serializers.Serializer):
    sub_category = serializers.PrimaryKeyRelatedField(
        queryset=models.SubCategories.objects.filter(is_active=True))
    original_price = serializers.FloatField()
    offer_price = serializers.FloatField()
    stock_qty = serializers.IntegerField()
    pricing_category = serializers.PrimaryKeyRelatedField(
        queryset=models.PricingCategories.objects.all())
    product_image = serializers.ImageField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass
