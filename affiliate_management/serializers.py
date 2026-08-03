from annoying.functions import get_object_or_None
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers, exceptions

from categories.serializers import CountriesSerializers, NameSerializers
from offers_management.serializers import CouponSerializers
from orders_management.models import Orders
from product_management.models import Products
from space_and_beauty import constants
from . import models, utils


class OTPVerificationSerializer(serializers.Serializer):
    otp = serializers.IntegerField(min_value=000000, max_value=999999)
    client = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class CreateOfferSerializer(serializers.Serializer):
    offer_code = serializers.CharField()
    referral_code = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = models.User
        fields = ("id", "first_name", "last_name", "email", "username",)

    def validate_email(self, email):
        user = self.context['request'].user
        if user.is_authenticated:
            is_email = models.User.objects.filter(email=email).exclude(id=user.id)
        else:
            is_email = get_object_or_None(self.Meta.model, email=email)

        if is_email:
            raise exceptions.ValidationError(constants.EMAIL_ALREADY_EXISTS)

        return email

    def validate_username(self, username):

        user = get_object_or_None(self.Meta.model, username=username)
        if user:
            raise exceptions.ValidationError(constants.USERNAME_ALREADY_EXISTS)

        return username


class WalletHistorySerializers(serializers.ModelSerializer):
    currency = CountriesSerializers()

    class Meta:
        model = models.WalletHistory
        fields = ("id", "description", "amount", "is_credit", "created_on", "currency")


class AffiliatesSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    country = CountriesSerializers(read_only=True)
    phone_code = CountriesSerializers(read_only=True)
    payment_type = NameSerializers(read_only=True)

    country_id = serializers.PrimaryKeyRelatedField(queryset=models.Countries.objects.all(), write_only=True)
    phone_code_id = serializers.PrimaryKeyRelatedField(queryset=models.Countries.objects.all(), write_only=True)
    payment_type_id = serializers.PrimaryKeyRelatedField(queryset=models.PaymentType.objects.all(), write_only=True)
    referral_code = serializers.CharField(read_only=True)
    token = serializers.CharField(required=False)
    offer = CouponSerializers(read_only=True)

    class Meta:
        model = models.Affiliates
        fields = ("id", "user", "phone_code", "door_no", "street_address", "city", "state", "country", "referral_code",
                  "country_id", "postal_code", "payment_type", "payment_details", "phone_code_id", "payment_type_id",
                  "social_media", "token", "offer", "total_amount", "total_paid", "wallet_amount")

    @transaction.atomic()
    def create(self, validated_data):
        validated_data.pop("user")
        user = self.context['request'].data['user']

        user_serializer = UserSerializer(data=user, context={"request": self.context['request']})
        if not user_serializer.is_valid():
            raise exceptions.ValidationError(user_serializer.errors)

        validated_data['user'] = user_serializer.save()
        validated_data['phone_code'] = validated_data.pop("phone_code_id")
        validated_data['country'] = validated_data.pop("country_id")
        validated_data['payment_type'] = validated_data.pop("payment_type_id")
        validated_data['referral_code'] = utils.generate(8)

        return self.Meta.model.objects.create(**validated_data)


class BarterEligibilityProduct(serializers.ModelSerializer):
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Products
        fields = ("id", "title", "thumbnail_image", "is_barter_order_count", "is_available")

    @staticmethod
    def get_is_available(obj):
        return False


class ListAffiliatesSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    country = CountriesSerializers(read_only=True)
    offer = CouponSerializers(read_only=True)
    total_sales = serializers.SerializerMethodField()
    total_earning = serializers.SerializerMethodField()

    class Meta:
        model = models.Affiliates
        fields = ("id", "user", "country", "offer", "total_amount", "total_sales", "total_earning", "created_on")

    @staticmethod
    def get_total_earning(obj):
        return (obj.total_amount / 100) * 20

    @staticmethod
    def get_total_sales(obj):
        if obj.offer:
            order = Orders.objects.filter(is_success=True, coupon=obj.offer).count()
            return order
        return 0
