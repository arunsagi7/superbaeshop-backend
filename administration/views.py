from datetime import datetime, timedelta

import django.contrib.auth.signals
from django.db.models import Q, Sum, Count
from django.db.models.functions import TruncDay
from django.utils.timezone import now
from rest_framework import generics, exceptions, response, permissions, status

from accounts.models import UserProfile
from administration import serializers, utils
from affiliate_management.models import Affiliates
from affiliate_management.serializers import ListAffiliatesSerializer
from authentication.utils import ActionViewMixin, User, get_or_create_token
from categories.templatetags.site_tags import increase_decrease_per
from orders_management.models import Orders
from orders_management.serializers import OrdersSerializer
from orders_management.utils import str2bool
from space_and_beauty import constants
from space_and_beauty.pagination import RestFrameworkPaginationMixin


class LoginView(ActionViewMixin, generics.GenericAPIView):
    """
    use this endpoint to login an user (obtain authentication token).
    """
    serializer_class = serializers.LoginSerializer

    def action(self, serializer):
        user = self.validate_user(serializer)
        user.token = get_or_create_token(user, serializer.data).key

        django.contrib.auth.signals.user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        data = serializers.UserSerializer(user, context={'request': self.request}).data
        return response.Response(data=data)

    @staticmethod
    def validate_user(serializer):
        username = serializer.data['username']
        try:
            user = User.objects.get(Q(username=username, is_staff=True) |
                                    Q(email=username, is_staff=True))
        except User.DoesNotExist:
            raise exceptions.ValidationError({"non_field_errors": constants.UNAUTHORISED_USER})

        if user.is_active:
            if user.check_password(serializer.data['password']):
                return user
            raise exceptions.ValidationError({"non_field_errors": constants.INVALID_CREDENTIALS_ERROR})

        raise exceptions.NotAcceptable({"non_field_errors": constants.INACTIVE_ACCOUNT_ERROR, "id": user.id,
                                        "username": user.username})


class LogoutView(generics.GenericAPIView):
    """
    Use this endpoint to logout an user (remove user authentication token).
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(self, request):
        if request.auth:
            request.auth.delete()
            django.contrib.auth.signals.user_logged_out.send(sender=request.user.__class__, request=request,
                                                             user=self.request.user)
        return response.Response(status=status.HTTP_200_OK, data={"redirect": "/"})


class DashboardStatusView(generics.GenericAPIView):
    permission_classes = (
        permissions.IsAdminUser,
    )

    def get(self, request):
        data = dict()
        if "country" in request.query_params and self.request.query_params['country']:
            revenue_order = Orders.objects.filter(address__country=request.query_params['country'], is_success=True,
                                                  status__order_status__in=[1, 2, 3, 4])
            order = Orders.objects.filter(is_success=True, status__order_status__in=[1, 2, 3, 4])
        else:
            order = Orders.objects.filter(is_success=True, status__order_status__in=[1, 2, 3, 4])
            revenue_order = Orders.objects.filter(is_success=True, status__order_status__in=[1, 2, 3, 4])

        today = datetime.today()

        last_3_month = datetime.now() - timedelta(days=90)
        last_6_month = datetime.now() - timedelta(days=180)

        last_month = today.replace(day=1) - timedelta(days=1)

        ge_today_order = order.filter(created_on__date=now().date()).count()

        ge_yesterday_order = order.filter(created_on__date=(datetime.now() - timedelta(days=1)).date()).count()
        ge_two_day_order = order.filter(created_on__date=(datetime.now() - timedelta(days=2)).date()).count()

        ge_this_week_order = order.filter(created_on__week=int(now().strftime("%V")),
                                          created_on__year=today.year).count()
        ge_last_week_order = order.filter(created_on__week=int(now().strftime("%V")) - 1,
                                          created_on__year=today.year).count()

        ge_this_month_order = order.filter(created_on__month=today.month, created_on__year=today.year).count()
        ge_last_month_order = order.filter(created_on__month=last_month.month, created_on__year=last_month.year).count()

        ge_last_3_month_order = order.filter(created_on__month__gte=last_3_month.month,
                                             created_on__year=last_3_month.year).count()
        ge_last_6_month_order = order.filter(created_on__month__gte=last_6_month.month,
                                             created_on__year=last_6_month.year).count()

        data['today_order'] = ge_today_order
        data['today_order_per'] = increase_decrease_per(ge_today_order, ge_yesterday_order)

        data['yesterday_order'] = ge_yesterday_order
        data['yesterday_order_per'] = increase_decrease_per(ge_yesterday_order, ge_two_day_order)

        data['this_week'] = ge_this_week_order
        data['this_week_per'] = increase_decrease_per(ge_this_week_order, ge_last_week_order)

        data['total_month'] = ge_this_month_order
        data['total_month_per'] = increase_decrease_per(ge_this_month_order, ge_last_month_order)

        data['ge_last_3_month_order'] = ge_last_3_month_order
        data['ge_last_3_month_per'] = 0

        data['ge_last_6_month_order'] = ge_last_6_month_order
        data['ge_last_6_month_per'] = 0

        today_order, today_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__date": now().date()})

        yesterday_order, yesterday_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__date": datetime.now() - timedelta(days=1)})

        two_day_order, two_day_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__date": datetime.now() - timedelta(days=2)})

        this_week_order, this_week_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__week": int(now().strftime("%V")), "created_on__year": today.year})
        last_week_order, last_week_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__week": int(now().strftime("%V")) - 1,  "created_on__year": today.year})

        this_month_order, this_month_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__month": today.month, "created_on__year": today.year})

        last_month_order, last_month_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__month": today.month, "created_on__year": today.year})

        last_3_months_order, last_3_months_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__month__gte": last_3_month.month - 3, "created_on__year": last_3_month.year})

        last_6_months_order, last_6_months_revenue = utils.revenue_order_calculation(revenue_order, {
            "created_on__month__gte": last_6_month.month - 6, "created_on__year": last_6_month.year})

        data['transaction'] = [
            {

                "count_revenue": round(today_revenue, 2),
                "percentage_revenue": increase_decrease_per(today_revenue, yesterday_revenue),
                "name": "Total order Today",
                "sub_name": "from yesterday",
                "count": today_order,
                "percentage": increase_decrease_per(today_order, yesterday_order)

            },
            {
                "count_revenue": round(yesterday_revenue, 2),
                "percentage_revenue": increase_decrease_per(yesterday_revenue, two_day_revenue),
                "name": "Total order Yesterday",
                "sub_name": "from day before",
                "count": yesterday_order,
                "percentage": increase_decrease_per(yesterday_order, two_day_order)
            },
            {
                "count_revenue": round(this_week_revenue, 2),
                "percentage_revenue": increase_decrease_per(this_week_revenue, last_week_revenue),
                "name": "Total order This Week",
                "sub_name": "from last week",
                "count": this_week_order,
                "percentage": increase_decrease_per(this_week_order, last_week_order)
            },
            {
                "count_revenue": round(this_month_revenue, 2),
                "percentage_revenue": increase_decrease_per(this_month_revenue, last_month_revenue),
                "name": "Total order This Month",
                "sub_name": "from last Month",
                "count": this_month_order,
                "percentage": increase_decrease_per(this_month_order, last_month_order)
            },
            {
                "count_revenue": round(last_3_months_revenue, 2),
                "percentage_revenue": increase_decrease_per(0, 0),
                "name": "Last 3 Months Order",
                "sub_name": "from 6 Month",
                "count": last_3_months_order,
                "percentage": increase_decrease_per(0, 0)
            },
            {
                "count_revenue": round(last_6_months_revenue, 2),
                "percentage_revenue": increase_decrease_per(0, 0),
                "name": "Last 6 Months Order",
                "sub_name": "No Data",
                "count": last_6_months_order,
                "percentage": increase_decrease_per(0, 0)
            }
        ]

        data['order_per_day'] = list(revenue_order.filter(created_on__month=now().month,
                                                          created_on__year=now().year).annotate(
            day=TruncDay('created_on')).values('day').annotate(total=Count('id')))

        data['last_15_days'] = list(
            revenue_order.filter(created_on__date__gte=datetime.now() - timedelta(days=15)).annotate(
                day=TruncDay('created_on')).values('day').annotate(total=Count('id'),
                                                                   amount=Sum("pay_amount")).order_by("-day"))

        return response.Response(data)


class OrdersViewSet(generics.ListAPIView):
    """
    use this endpoint do following operations
    1. COD Checkout
    2. Online Checkout
    """
    permission_classes = (
        permissions.IsAdminUser,
    )
    serializer_class = OrdersSerializer
    pagination_class = RestFrameworkPaginationMixin

    def get_queryset(self):
        filter_dict = {}

        if "status" in self.request.query_params and self.request.query_params['status']:
            if int(self.request.query_params['status']) == 0:
                filter_dict['is_success'] = False
                if "read_status" in self.request.query_params and self.request.query_params['read_status']:
                    filter_dict['is_read'] = str2bool(self.request.query_params['read_status'])
            else:
                filter_dict['is_success'] = True

        return Orders.objects.filter(**filter_dict).order_by("-created_on")


class OrdersStatusViewSet(generics.UpdateAPIView):
    """
    """
    permission_classes = (
        permissions.IsAdminUser,
    )
    serializer_class = serializers.OrderUpdateSerializer
    queryset = Orders.objects.all()


class UserProfileView(generics.ListAPIView):
    """
    use this endpoint to show user details
    """
    permission_classes = (
        permissions.IsAdminUser,
    )
    serializer_class = serializers.UserProfileSerializers
    pagination_class = RestFrameworkPaginationMixin

    def get_queryset(self):
        return UserProfile.objects.all().order_by("-user__date_joined")


class AffiliateView(generics.ListAPIView):
    """
    use this endpoint to show user details
    """
    permission_classes = (
        permissions.IsAdminUser,
    )
    serializer_class = ListAffiliatesSerializer
    pagination_class = RestFrameworkPaginationMixin

    def get_queryset(self):
        return Affiliates.objects.all().order_by("-created_on")


class CartUserView(generics.ListAPIView):
    """
    use this endpoint to show user details
    """
    permission_classes = (
        permissions.IsAdminUser,
    )
    serializer_class = serializers.UserProfileSerializers
    pagination_class = RestFrameworkPaginationMixin

    def get_queryset(self):
        return UserProfile.objects.filter(my_cart__isnull=False).order_by("-my_cart__created_on")


class AdminMenuView(generics.GenericAPIView):
    """
    use this endpoint to get all available admin menu tabs
    """
    permission_classes = (
        permissions.IsAdminUser,
    )

    def get(self, request):
        menu_items = [
            {
                "id": 1,
                "name": "Orders",
                "icon": "shopping-bag",
                "url": "/admin/orders",
                "description": "Manage all orders"
            },
            {
                "id": 2,
                "name": "Offers",
                "icon": "gift",
                "url": "/admin/offers",
                "description": "Manage promotional offers"
            },
            {
                "id": 3,
                "name": "Affiliate",
                "icon": "users",
                "url": "/admin/affiliate",
                "description": "Manage affiliate program"
            },
            {
                "id": 4,
                "name": "Users",
                "icon": "user",
                "url": "/admin/users",
                "description": "Manage user accounts"
            },
            {
                "id": 5,
                "name": "Products",
                "icon": "box",
                "url": "/admin/products",
                "description": "Manage product catalog"
            },
            {
                "id": 6,
                "name": "Blog",
                "icon": "book",
                "url": "/admin/blog",
                "description": "Manage blog posts"
            },
            {
                "id": 7,
                "name": "Cart",
                "icon": "shopping-cart",
                "url": "/admin/cart",
                "description": "Manage user carts"
            },
            {
                "id": 8,
                "name": "Categories",
                "icon": "layers",
                "url": "/admin/categories",
                "description": "Manage product categories"
            },
            {
                "id": 9,
                "name": "Others",
                "icon": "ellipsis-h",
                "url": "/admin/others",
                "description": "Other management options"
            },
            {
                "id": 10,
                "name": "Tokens",
                "icon": "key",
                "url": "/admin/tokens",
                "description": "Manage authentication tokens"
            },
            {
                "id": 11,
                "name": "Homebanner",
                "icon": "film",
                "url": "/admin/homebanner",
                "description": "Manage hero banner videos"
            },
        ]
        return response.Response(data={"menu_items": menu_items, "count": len(menu_items)})
