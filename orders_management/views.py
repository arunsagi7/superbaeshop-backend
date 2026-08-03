import hashlib
import hmac
from threading import Thread
from urllib.parse import urlencode

import requests
from django.db import transaction
from rest_framework import viewsets, permissions, exceptions, mixins, generics, response
from rest_framework.decorators import action

from accounts.utils import user_point_history
from affiliate_management.utils import affiliate_price_calculation
from authentication.utils import SendOneTimePassword, SendEmailViewMixin
from categories.utils import int_to_country
from others.models import ShipmentLogin
from space_and_beauty.pagination import RestFrameworkPaginationMixin
from . import serializers, utils, models
from .Shipping_details import calculating_delivery_charges


class OrdersViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """
    use this endpoint do following operations
    1. COD Checkout
    2. Online Checkout
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )
    serializer_class = serializers.OrdersSerializer
    pagination_class = RestFrameworkPaginationMixin

    def get_queryset(self):
        return models.Orders.objects.filter(user=self.request.user.userprofile, is_success=True).order_by("-created_on")


class CheckoutViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.ListModelMixin):
    """
    use this endpoint do following operations
    1. COD Checkout
    2. Online Checkout
    3. List Checkout Items
    4. Delete Checkout Item
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )
    serializer_class = serializers.OrdersSerializer

    def get_queryset(self):
        return models.Orders.objects.filter(user=self.request.user.userprofile, is_success=False).order_by("-created_on")

    @action(detail=True, methods=['DELETE'])
    def cancel(self, request, pk=None):
        try:
            order = self.get_queryset().get(pk=pk)
            order.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except models.Orders.DoesNotExist:
            raise exceptions.NotFound("Checkout item not found")


class CODConfirmationView(generics.GenericAPIView, SendOneTimePassword, SendEmailViewMixin):
    """
    use this endpoint to confirm a cod order
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_template = "order_placed_sms.txt"
        self.subject_template_name = 'order_placed_subject.txt'
        self.html_body_template_name = 'order_placed_body.html'

    @transaction.atomic()
    def get(self, request, pk):
        order = utils.int_to_order(pk)
        if order.is_success:
            raise exceptions.NotFound()
        order.payment_status = True
        order.is_success = True
        if order.is_wallet:
            point = round(float(order.coupon_amount) / float(order.address.country.redeem_point_cash))
            user_point_history(order, point, True)

        elif order.coupon and hasattr(order.coupon, "affiliate_offer"):
            affiliate_price_calculation(order)

        order.save()

        for item in order.user.my_cart.all():
            item.product.stock_qty -= item.quantity
            item.product.save()

        order.user.my_cart.all().delete()
        serializer = serializers.OrdersSerializer(order, context={"request": request}).data

        self.sms_context = {"order": order}

        Thread(target=self.send_verification_otp, args=(order.user.user,),
               kwargs={"template_id": "1307162572047837798"}).start()

        Thread(target=self.send_email, args=(order.user.user.email, self.sms_context,)).start()
        Thread(target=utils.push_notification, args=(1, order)).start()

        return response.Response(serializer)


class PaymentSuccess(generics.GenericAPIView, SendOneTimePassword, SendEmailViewMixin):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_template = "order_placed_sms.txt"
        self.subject_template_name = 'order_placed_subject.txt'
        self.html_body_template_name = 'order_placed_body.html'

    @transaction.atomic()
    def post(self, request):
        serializer = serializers.PaymentSuccessSerializer(data=request.data)

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        payment_info = utils.int_payment_id(serializer.data['razorpay_order_id'])
        string = str(serializer.data['razorpay_order_id']) + "|" + str(serializer.data['razorpay_payment_id'])

        dig = hmac.new(utils.YOUR_API_SECRET.encode('utf-8'), msg=string.encode('utf-8'),
                       digestmod=hashlib.sha256).hexdigest()

        if str(dig) == str(serializer.data['razorpay_signature']):
            payment_info.payment_status = True
            payment_info.payment_id = serializer.data['razorpay_payment_id']
            payment_info.is_success = True
            payment_info.save()

            if payment_info.is_wallet:
                point = round(float(payment_info.coupon_amount) / float(payment_info.address.country.redeem_point_cash))
                user_point_history(payment_info, point, True)

            elif payment_info.coupon and hasattr(payment_info.coupon, "affiliate_offer"):
                affiliate_price_calculation(payment_info)

            for item in payment_info.user.my_cart.all():
                item.product.stock_qty -= item.quantity
                item.product.save()

            payment_info.user.my_cart.all().delete()

            self.sms_context = {"order": payment_info}

            Thread(target=self.send_verification_otp, args=(payment_info.user.user,),
                   kwargs={"template_id": "1307162572047837798"}).start()

            Thread(target=self.send_email, args=(payment_info.user.user.email, self.sms_context,)).start()
            Thread(target=utils.push_notification, args=(2, payment_info)).start()
            serializer = serializers.OrdersSerializer(payment_info, context={"request": request})
            return response.Response(serializer.data)
        else:
            raise exceptions.ValidationError({"non_field_errors": ["Signature mismatch."]})


class InfluencerOrderViewSet(generics.CreateAPIView):
    """
    use this endpoint to create influencer order
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    serializer_class = serializers.InfluencerOrderSerializers


class OrderToEmailView(generics.GenericAPIView, SendEmailViewMixin):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_context = {}
        self.subject_template_name = 'order_placed_subject.txt'
        self.html_body_template_name = 'order_placed_body.html'

    def get(self, request, pk):
        order = utils.int_to_order(pk)

        self.sms_context = {"order": order}

        Thread(target=self.send_email, args=(order.user.user.email, self.sms_context,)).start()
        serializer = serializers.OrdersSerializer(order, context={"request": request}).data
        return response.Response(serializer)


class GetOrderTrackingLink(generics.GenericAPIView):
    def get(self, request, pk):
        order = utils.int_to_order(pk)

        try:
            login_details = ShipmentLogin.objects.get(pk=1)
            token = login_details.token
        except ShipmentLogin.DoesNotExist:
            return response.Response({"error": "Shipment login details not configured"}, status=400)
        url = "https://apiv2.shiprocket.in/v1/external/courier/track/awb/{awb}".format(awb=order.awb_code)
        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {token}'.format(token=token)
        }
        tracking_response = requests.request("GET", url, headers=headers, data=payload)
        if tracking_response.status_code == 200:
            order_result = tracking_response.json()
            if "shipment_track" in order_result['tracking_data']:
                order.track_url = order_result['tracking_data']['track_url']
                order.save()
        serializer = serializers.OrdersSerializer(order, context={"request": request}).data
        return response.Response(serializer)


class CalculateDeliveryAmountView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get(self, request):
        if not request.query_params.get("country", None):
            raise exceptions.ValidationError({"country": ["Query Params country is missing"]})

        from django.db.models import Sum
        weight = request.user.userprofile.my_cart.aggregate(weight=Sum('product__weight'))['weight']

        weight = weight if weight else 1

        country = int_to_country(request.query_params.get("country", 1))
        if request.query_params.get("delivery_postcode", None):
            amount = calculating_delivery_charges(delivery_postcode=request.query_params.get("delivery_postcode", None),
                                                  country=country, weight=weight)
        else:

            country = int_to_country(request.query_params.get("country", 1))
            amount = country.shipping_fee

        return response.Response({"amount": amount})
