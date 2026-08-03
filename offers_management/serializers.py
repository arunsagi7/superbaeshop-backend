from rest_framework import serializers

from . import models


class CouponSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Coupon
        fields = ("id", "title", "payout", "image", "offer_code")


class OfferTermsSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.OfferTerms
        fields = ("icon", "title", "created_on")


class OfferSerializers(serializers.ModelSerializer):
    terms = OfferTermsSerializers(many=True)
    type = serializers.CharField(source='get_type_display')

    class Meta:
        model = models.Offers
        fields = ("type", "title", "min_product", "offer_value", "max_discount", "short_descriptions", "terms")
