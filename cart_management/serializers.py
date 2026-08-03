from datetime import datetime, timedelta

from annoying.functions import get_object_or_None
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from rest_framework import serializers, exceptions

from cart_management import models
from categories.serializers import CountriesSerializers
from product_management.models import ProductAvailableCountries, Products
from space_and_beauty import constants


class ProductAvailableCountriesSerializer(serializers.ModelSerializer):
    country = CountriesSerializers()

    class Meta:
        model = ProductAvailableCountries
        fields = ("id", "country", "product", "original_price", "selling_price", "promotion_text")


class ListProductsSerializer(serializers.ModelSerializer):
    product_country = ProductAvailableCountriesSerializer(many=True)
    in_cart = serializers.SerializerMethodField()
    thumbnail_image = serializers.SerializerMethodField()
    from product_management.serializers import ProductImagesSerializers
    product_images = ProductImagesSerializers(many=True, read_only=True)

    class Meta:
        model = Products
        fields = ("id", "sku", "title", "slug", "thumbnail_image", "product_images", "product_country", "in_cart", "stock_status")

    def get_in_cart(self, obj):
        user = self.context['request'].user
        if user.is_authenticated and hasattr(user, "userprofile"):
            cart = get_object_or_None(models.Cart, product=obj, user=user.userprofile)
            if cart:
                return {"id": cart.id, "quantity": cart.quantity, }
        return None

    def get_thumbnail_image(self, obj):
        request = self.context.get('request')
        user = self.context.get('request').user if request else None
        cart = None
        if user and user.is_authenticated and hasattr(user, "userprofile"):
            cart = get_object_or_None(models.Cart, product=obj, user=user.userprofile)
        if cart and cart.color_code == "black":
            return "https://api.spaceandbeauty.com/media/product/product-image/planner_black-01c937f5ae76e1f7b514b80fb572bf8e.png"
        
        if obj.thumbnail_image:
            photo_url = obj.thumbnail_image.url
            return request.build_absolute_uri(photo_url) if request else photo_url
            
        from categories.models import HomepageSectionProduct
        hsp = HomepageSectionProduct.objects.filter(product=obj).exclude(image__isnull=True).exclude(image='').first()
        if hsp and hsp.image:
            # These images are frontend assets (e.g. /images/...) so return them as-is
            return hsp.image
            
        return None


class CartSerializers(serializers.ModelSerializer):
    product = ListProductsSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    offer_avail = serializers.SerializerMethodField()

    class Meta:
        model = models.Cart
        fields = ("id", "product", "quantity", "created_on", "product_id", "is_offer", "offer_avail", "color_code")

    def create(self, validated_data):
        if not hasattr(self.context['request'].user, "userprofile"):
            raise exceptions.NotAcceptable()

        # Get product by ID with better error handling
        product_id = validated_data.pop("product_id")
        try:
            product = Products.objects.get(pk=product_id)
        except Products.DoesNotExist:
            raise exceptions.ValidationError({"product_id": [f"Invalid pk \"{product_id}\" - object does not exist."]})
        
        validated_data['user'] = self.context['request'].user.userprofile
        validated_data['product'] = product

        if validated_data['quantity'] == 0:
            try:
                cart = self.Meta.model.objects.get(user=validated_data['user'],
                                                   product=validated_data['product'])
                cart.delete()
                return None
            except ObjectDoesNotExist:
                return None
        else:

            if validated_data['product'].stock_qty < 1:
                raise exceptions.ValidationError({"non_field_errors": [constants.OUT_OF_STOCK]})

            if validated_data['product'].stock_qty < validated_data['quantity']:
                raise exceptions.ValidationError(
                    {"non_field_errors": [
                        constants.STOCK_EXISTS_CART_ITEM.format(validated_data['product'].stock_qty)]})

            cart, _ = self.Meta.model.objects.get_or_create(user=validated_data['user'],
                                                             product=validated_data['product'],
                                                             defaults=dict(**validated_data))

            if not _ and validated_data['quantity'] != 0:
                cart.quantity = validated_data['quantity']
                cart.save()
            return cart

    @staticmethod
    def get_offer_avail(obj):
        cart_date = obj.created_on + timedelta(days=1)

        if cart_date < datetime.today():
            return False
        return obj.is_offer


class GuestCartSerializers(serializers.ModelSerializer):
    product = ListProductsSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    offer_avail = serializers.SerializerMethodField()
    session_id = serializers.CharField(write_only=True)

    class Meta:
        model = models.GuestCart
        fields = ("id", "session_id", "product", "quantity", "created_on", "product_id", "is_offer", "offer_avail", "color_code")

    def create(self, validated_data):
        product_id = validated_data.pop("product_id")
        try:
            product = Products.objects.get(pk=product_id)
        except Products.DoesNotExist:
            raise exceptions.ValidationError({"product_id": [f"Invalid pk \"{product_id}\" - object does not exist."]})
        
        validated_data['product'] = product
        session_id = validated_data.get('session_id')

        if validated_data['quantity'] == 0:
            try:
                cart = self.Meta.model.objects.get(session_id=session_id, product=validated_data['product'])
                cart.delete()
                return None
            except ObjectDoesNotExist:
                return None
        else:
            if validated_data['product'].stock_qty < 1:
                raise exceptions.ValidationError({"non_field_errors": [constants.OUT_OF_STOCK]})

            if validated_data['product'].stock_qty < validated_data['quantity']:
                raise exceptions.ValidationError(
                    {"non_field_errors": [
                        constants.STOCK_EXISTS_CART_ITEM.format(validated_data['product'].stock_qty)]})

            cart, _ = self.Meta.model.objects.get_or_create(session_id=session_id,
                                                             product=validated_data['product'],
                                                             defaults=dict(**validated_data))

            if not _ and validated_data['quantity'] != 0:
                cart.quantity = validated_data['quantity']
                cart.save()
            return cart

    @staticmethod
    def get_offer_avail(obj):
        cart_date = obj.created_on + timedelta(days=1)

        if cart_date < datetime.today():
            return False
        return obj.is_offer