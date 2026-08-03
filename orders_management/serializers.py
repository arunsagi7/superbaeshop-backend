from datetime import datetime
from threading import Thread

from annoying.functions import get_object_or_None
from django.db import transaction
from django.db.models import Sum
from rest_framework import serializers, exceptions

import razorpay
from accounts.serializers import AddressSerializer
from categories.serializers import CountriesSerializers
from offers_management.serializers import CouponSerializers
from offers_management.utils import code_coupon
from . import models, utils


class ListProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Products
        fields = ("id", "sku", "title", "slug", "thumbnail_image")


class OrderItemsSerializer(serializers.ModelSerializer):
    currency = CountriesSerializers()
    product = ListProductsSerializer()

    class Meta:
        model = models.OrderItems
        fields = ("id", "product", "quantity", "currency", "unit_price", "offer_title", "offer_amount", "gst", "color")


class OrdersSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    address_id = serializers.PrimaryKeyRelatedField(queryset=models.Address.objects.all(), write_only=True)
    offer = CouponSerializers(read_only=True)
    status = serializers.CharField(read_only=True)
    order_items = OrderItemsSerializer(many=True, read_only=True)
    api_key = serializers.SerializerMethodField()
    amount_in_paisa = serializers.SerializerMethodField()
    affiliate_earnings = serializers.SerializerMethodField()
    selected_country = serializers.SerializerMethodField()
    currency_type = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.Orders
        fields = ("id", "tracking_client_id", "address", "status", "payment_type", "total_amount", "offer",
                  "coupon_amount", "pay_amount", "shipping_charge", "cod_charge", "other_charge", "created_on",
                  "order_items", "coupon_code", "coupon", "name", "email", "phone", "dial_code", "address_id",
                  "alt_phone", "alt_dial_code", "order_items", "is_read", "api_key", "is_wallet", "amount_in_paisa",
                  "sub_total_amount", "transaction_id", "affiliate_earnings", "awb_code", "track_url",
                  "discount_amount", "total_gst", "currency_type", "selected_country")

    @transaction.atomic()
    def create(self, validated_data):
        request = self.context['request']
        userprofile = request.user.userprofile
        coupon = validated_data.get("coupon_code", None)
        delivery_charge = request.data.get("delivery_charge", None)
        is_wallet = validated_data.get("is_wallet", None)
        
        # Get country_code from request data (sent from frontend based on URL country)
        country_code = request.data.get("country_code", None)
        
        validated_data['address'] = validated_data.pop("address_id")
        address = validated_data['address']
        
        # Use the selected country from URL if provided, otherwise use address country
        if country_code:
            from categories.models import Countries
            try:
                selected_country = Countries.objects.get(code2=country_code.lower())
                validated_data['currency_type'] = selected_country.currency_type
            except Countries.DoesNotExist:
                validated_data['currency_type'] = address.country.currency_type
        else:
            validated_data['currency_type'] = address.country.currency_type
        if is_wallet:
            pass
        elif coupon:
            coupon = code_coupon(coupon)
            validated_data['coupon'] = coupon

        validated_data['user'] = userprofile
        now = datetime.now()
        try:
            object_id = self.Meta.model.objects.latest("id").id if self.Meta.model.objects.latest("id") else 0
        except:
            object_id = 0
        validated_data['tracking_client_id'] = "S&B-{}-{:04d}".format(now.strftime("%d%m"), object_id + 1)
        order = self.Meta.model.objects.create(**validated_data)

        # Get the selected country for price calculation
        from categories.models import Countries
        if country_code:
            try:
                selected_country = Countries.objects.get(code2=country_code.lower())
                calculation_country = selected_country
            except Countries.DoesNotExist:
                calculation_country = address.country
        else:
            calculation_country = address.country

        checkout_amount = utils.calculate_amount(userprofile, order, country=calculation_country, offer=coupon,
                                                 is_wallet=is_wallet, delivery_charge=delivery_charge)
        order.total_amount = checkout_amount['total_amount']
        order.coupon_amount = checkout_amount['coupon_amount']
        order.pay_amount = checkout_amount['pay_amount']
        order.shipping_charge = checkout_amount['shipping_charge']
        order.cod_charge = checkout_amount['cod_charge']
        order.other_charge = checkout_amount['other_charge']
        order.total_gst = checkout_amount['total_gst']

        if not request.user.first_name:
            request.user.first_name = validated_data['name']
            request.user.save()

        cod = False if validated_data['payment_type'] == "Online" else True

        if not cod:
            client = razorpay.Client(auth=(utils.YOUR_API_KEY, utils.YOUR_API_SECRET))
            try:
                # Use the selected country's currency for payment
                payment_currency = calculation_country.currency_type
                resp = client.order.create(
                    data={'currency': payment_currency, 'receipt': userprofile.user.username,
                          'payment_capture': True, 'amount': checkout_amount['razor_pay']})
            except Exception as e:
                raise exceptions.ValidationError({"non_field_errors": [str(e)]})

            order.transaction_id = resp['id']

        order.save()

        Thread(target=utils.push_notification, args=(2, order)).start()

        return order

    @staticmethod
    def get_api_key(order):
        if order.payment_type == "Online":
            return utils.YOUR_API_KEY
        return None

    @staticmethod
    def get_amount_in_paisa(order):
        return int(order.pay_amount * 100)

    def get_affiliate_earnings(self, order):
        user = self.context['request'].user
        total_earnings = 0
        if hasattr(user, "affiliates"):
            for item in order.order_items.all():
                price = item.quantity * item.unit_price
                total_earnings += ((price / 100) * item.product.affiliate_percentage)
        return total_earnings

    def get_selected_country(self, order):
        # Return the country object based on the order's currency_type
        # Since multiple countries can have the same currency, we need to find the right one
        from categories.models import Countries
        
        # First, try to get the country from the address if available
        if order.address and order.address.country:
            address_country = order.address.country
            # Check if address country's currency matches the order's currency_type
            if address_country.currency_type == order.currency_type:
                return CountriesSerializers(address_country, context=self.context).data
        
        # If address country doesn't match, try to find any country with matching currency
        # Use filter().first() to avoid MultipleObjectsReturned error
        country = Countries.objects.filter(currency_type=order.currency_type).first()
        if country:
            return CountriesSerializers(country, context=self.context).data
        
        # Fallback to address country if no matching currency found
        if order.address and order.address.country:
            return CountriesSerializers(order.address.country, context=self.context).data
        
        return None


class CreateOrderSerializer(serializers.Serializer):
    address = serializers.PrimaryKeyRelatedField(queryset=models.Address.objects.all())
    payment_type = serializers.ChoiceField(choices=models.PAYMENT_TYPE_CHOICES)
    coupon_code = serializers.CharField(required=False)

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class PaymentSuccessSerializer(serializers.Serializer):
    razorpay_order_id = serializers.CharField()
    razorpay_payment_id = serializers.CharField()
    razorpay_signature = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class InfluencerOrderSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.InfluencerOrder
        fields = ("id", "product")

    def create(self, validated_data):
        user = self.context['request'].user

        if hasattr(user, "affiliates"):
            cart = get_object_or_None(models.InfluencerOrder, product=validated_data['product'],
                                      affiliates=user.affiliates)
            if cart:
                raise exceptions.ValidationError({"non_field_errors": ["Already Ordered This product"]})

            quantity = validated_data['product'].product_order.filter(order__coupon=user.affiliates.offer
                                                                      ).aggregate(quantity=Sum('quantity'))[
                'quantity']

            if not (quantity >= validated_data['product'].is_barter_order_count):
                raise exceptions.ValidationError({"non_field_errors": ["You are not eligible to order this product."]})
        else:
            raise exceptions.ValidationError({"non_field_errors": ["Already Ordered This product"]})

        validated_data['affiliates'] = user.affiliates
        return self.Meta.model.objects.create(**validated_data)
