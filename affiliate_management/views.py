import datetime
from threading import Thread

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import viewsets, exceptions, response, permissions
from rest_framework.decorators import action

from affiliate_management import serializers, utils, models
from authentication.serializers import LoginSerializer
from authentication.utils import SendOneTimePassword, random_digits, get_or_create_token
from offers_management.utils import exits_code_coupon
from orders_management.models import Orders
from orders_management.serializers import OrdersSerializer
from product_management.models import Products
from space_and_beauty import constants
from space_and_beauty.pagination import PaginationMixin


class AffiliatesViewSet(viewsets.GenericViewSet, SendOneTimePassword, PaginationMixin):
    """
    use this endpoint to do following operations
    1. Crate Affiliates
    2. Verify Affiliates
    3. Create Affiliate's Offer code
    4. Resend Verification for Affiliates
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_template = "otp_affiliate_send_sms.txt"
        self.page_max_size = 8
        self.model = None

    serializer_class = serializers.AffiliatesSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            affiliates = serializer.save()

            self.sms_context = {"user": affiliates.user, "otp": affiliates.otp}
            now = datetime.datetime.now()

            if not affiliates.otp or affiliates.otp_expired.time() < now.time():
                affiliates.otp = random_digits(6)

            if not affiliates.otp_expired:
                affiliates.otp_expired = now + datetime.timedelta(minutes=30)

            affiliates.save()
        else:
            raise exceptions.ValidationError(serializer.errors)

        Thread(target=self.send_verification_otp, args=(affiliates.user,)).start()

        data = {"affiliates": affiliates.id,
                "data": "OTP sent to +{} {}".format(affiliates.phone_code.dial_code,
                                                    affiliates.user.username)}

        return response.Response(data)

    @action(detail=False, methods=["POST"])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        user = self.validate_user(serializer)
        affiliates = user.affiliates

        if not affiliates.is_active:
            raise exceptions.ValidationError({"non_field_errors": [constants.INACTIVE_ACCOUNT_ERROR]})

        self.sms_context = {"user": affiliates.user, "otp": affiliates.otp}
        now = datetime.datetime.now()

        if not affiliates.otp or affiliates.otp_expired.time() < now.time():
            affiliates.otp = random_digits(6)

        if not affiliates.otp_expired:
            affiliates.otp_expired = now + datetime.timedelta(minutes=30)

        affiliates.save()

        Thread(target=self.send_verification_otp, args=(affiliates.user,)).start()

        data = {"affiliates": affiliates.id,
                "data": "OTP sent to +{} {}".format(affiliates.phone_code.dial_code,
                                                    affiliates.user.username)}

        return response.Response(data)

    @transaction.atomic()
    @action(detail=True, methods=['POST'])
    def verify_otp(self, request, pk):
        serializer = serializers.OTPVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        affiliates = utils.int_to_affiliates(pk)

        if affiliates.otp != serializer.data['otp']:
            raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OTP_ERROR]})
        affiliates.otp = None
        affiliates.save()
        affiliates.token = get_or_create_token(affiliates.user, serializer.data["client"]).key

        return response.Response(self.get_serializer(affiliates, context={"request": request}).data)

    @transaction.atomic()
    @action(detail=False, methods=['POST'], permission_classes=(permissions.IsAuthenticated,))
    def create_offer(self, request):
        affiliates = request.user.affiliates
        serializer = serializers.CreateOfferSerializer(data=request.data)

        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        coupon_code = exits_code_coupon(serializer.data['offer_code'])
        if not coupon_code:
            coupon_code = utils.create_offers(affiliates.user.get_full_name(), serializer.data['offer_code'])
            affiliates.offer = coupon_code
            affiliates.save()
        else:
            raise exceptions.ValidationError({"coupon_code": [constants.INVALID_COUPON_EXITS_ERROR]})
        if "referral_code" in serializer.data:
            referral_by = utils.code_to_affiliates(serializer.data['referral_code'])

            if referral_by != affiliates:
                models.AffiliatesReferral.objects.get_or_create(referred_by=referral_by, referral=affiliates)
            else:
                raise exceptions.ValidationError(
                    {"non_field_errors": ["You can't refer you. Try another Referral offer code"]})

        return response.Response(self.get_serializer(affiliates, context={"request": request}).data)

    @staticmethod
    def validate_user(serializer):
        try:
            user = models.User.objects.get(username=serializer.data["username"])
            if not hasattr(user, "affiliates"):
                raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_USERNAME]})
        except ObjectDoesNotExist:
            raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_USERNAME]})
        return user

    @action(detail=False)
    def my_profile(self, request):
        affiliate = request.user.affiliates
        serializer = self.get_serializer(affiliate, context={"request": request})
        return response.Response(serializer.data)

    @action(detail=False)
    def my_wallet(self, request):
        if not hasattr(self.request.user, "affiliates"):
            raise exceptions.NotAuthenticated()
        data = dict()

        self.model = request.user.affiliates.wallet.all()

        qs = """self.model.order_by("-created_on")"""

        data['count'], data['prev'], data['next'], queryset = self.get_pagination_response(qs)
        serializer = serializers.WalletHistorySerializers(queryset, many=True, context={"request": request})
        data['results'] = serializer.data
        return response.Response(data)


class DashBoardViewSet(viewsets.GenericViewSet, PaginationMixin):
    """
    use this endpoint do following operations
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.page_max_size = 8
        self.model = None

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def list(self, request):
        data = dict()
        if not hasattr(self.request.user, "affiliates"):
            raise exceptions.NotAuthenticated()

        affiliate = request.user.affiliates
        now = datetime.datetime.now()
        order = Orders.objects.filter(coupon=affiliate.offer, created_on__year=now.year, is_success=True)
        data['today_order'] = order.filter(created_on__date=now.date()).count()
        yesterday = now.date() - datetime.timedelta(days=1)
        data['yesterday_order'] = order.filter(created_on__date=yesterday).count()
        data['thi_month_order'] = order.filter(created_on__month=now.month).count()
        data['thi_year_order'] = order.count()

        return response.Response(data)

    @action(detail=False)
    def my_order(self, request):
        if not hasattr(self.request.user, "affiliates"):
            raise exceptions.NotAuthenticated()
        data = dict()
        self.model = Orders

        qs = """self.model.objects.filter(coupon=self.request.user.affiliates.offer, is_success=True
        ).order_by("-created_on")"""

        data['count'], data['prev'], data['next'], queryset = self.get_pagination_response(qs)
        serializer = OrdersSerializer(queryset, many=True, context={"request": request})
        data['results'] = serializer.data
        return response.Response(data)

    @action(detail=False)
    def barter_eligibility(self, request):
        product = Products.objects.filter(is_active=True)
        serializer = serializers.BarterEligibilityProduct(product, many=True, context={"request": request})

        return response.Response(serializer.data)

    @action(detail=False)
    def sub_influence_dashboard(self, request):
        data = dict()
        if not hasattr(self.request.user, "affiliates"):
            raise exceptions.NotAuthenticated()

        affiliate = request.user.affiliates
        now = datetime.datetime.now()
        affiliate_offer = [x.referral.offer for x in affiliate.referred_by.filter(referral__offer__isnull=False)]
        order = Orders.objects.filter(is_success=True, coupon__in=affiliate_offer, created_on__year=now.year)
        data['today_order'] = order.filter(created_on__date=now.date()).count()
        yesterday = now.date() - datetime.timedelta(days=1)
        data['yesterday_order'] = order.filter(created_on__date=yesterday).count()
        data['thi_month_order'] = order.filter(created_on__month=now.month).count()
        data['thi_year_order'] = order.count()

        return response.Response(data)

    @action(detail=False)
    def list_sub_influence(self, request):

        if not hasattr(self.request.user, "affiliates"):
            raise exceptions.NotAuthenticated()
        data = dict()

        qs = """self.request.user.affiliates.referred_by.all().order_by("-referral__created_on")"""

        data['count'], data['prev'], data['next'], queryset = self.get_pagination_response(qs)
        final_data = [x.referral for x in queryset]
        serializer = serializers.ListAffiliatesSerializer(final_data, many=True, context={"request": request})
        data['results'] = serializer.data
        return response.Response(data)
