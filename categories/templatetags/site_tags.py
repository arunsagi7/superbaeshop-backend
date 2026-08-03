import calendar

from django import template
from django.db.models import Sum, Count
from django.db.models.functions import ExtractDay, TruncDay
from django.utils.timezone import now
from datetime import datetime, timedelta

from categories import models
from orders_management.models import Orders, OrderStatusMaster
from product_management.models import Products

register = template.Library()


def increase_decrease_per(new_value, old_value):
    if new_value is not None and old_value is not None:
        if int(new_value) == 0:
            return 0
        return round(((new_value - old_value) / new_value) * 100, 2)
    return 0


@register.simple_tag
def dashboard(request):
    data = dict()
    today = datetime.today()
    order = Orders.objects.filter(is_success=True).exclude(status__order_status__in=[5, 6])
    transactions = Orders.objects.filter(is_success=False).exclude(status__order_status__in=[5, 6])
    products_table = []
    order_status = OrderStatusMaster.objects.all().order_by("id")
    this_month_starting = today.replace(day=1)
    this_month_ending = today.replace(day=calendar.monthrange(today.year, today.month)[1])

    data['start_date'] = request.GET.get("start_date", this_month_starting.strftime("%Y-%m-%d"))
    data['end_date'] = request.GET.get("end_date", this_month_ending.strftime("%Y-%m-%d"))

    for status in order_status:
        row_dict = dict()
        row_dict['name'] = status.name
        product_qty = []
        for product in Products.objects.filter(id__in=[1, 2, 3, 4, 5], is_active=True):
            product_qty.append(product.product_order.filter(order__is_success=True,
                                                            order__created_on__date__range=[data['start_date'],
                                                                                            data['end_date']],
                                                            order__status__order_status__in=[status.id]).aggregate(
                qty=Sum("quantity"))['qty'])
        row_dict['product'] = product_qty
        products_table.append(row_dict)

    today_order = order.filter(created_on__date=now().date()).count()
    today_order_qty = order.filter(created_on__date=now().date()).aggregate(qty=Sum("order_items__quantity"))['qty']

    yesterday_order = order.filter(created_on__date=(datetime.now() - timedelta(days=1)).date()).count()
    two_day_order = order.filter(created_on__date=(datetime.now() - timedelta(days=2)).date()).count()

    yesterday_order_qty = order.filter(created_on__date=(datetime.now() - timedelta(days=1))).aggregate(
        qty=Sum("order_items__quantity"))['qty']

    this_week_order = order.filter(created_on__week=int(now().strftime("%V")), created_on__year=now().year).count()
    last_week_order = order.filter(created_on__week=int(now().strftime("%V")) - 1, created_on__year=now().year).count()

    this_week_order_qty = \
        order.filter(created_on__week=int(now().strftime("%V")), created_on__year=now().year).aggregate(
            qty=Sum("order_items__quantity"))['qty']

    this_month_order = order.filter(created_on__month=today.month, created_on__year=now().year).count()
    last_month_order = order.filter(created_on__month=(today.month - 1), created_on__year=now().year).count()

    this_month_order_qty = order.filter(created_on__month=today.month, created_on__year=now().year).aggregate(
        qty=Sum("order_items__quantity"))['qty']

    last_3_month = datetime.now() - timedelta(days=90)
    last_6_month = datetime.now() - timedelta(days=180)

    last_3_month_order = order.filter(created_on__month__gte=last_3_month.month,
                                      created_on__year__gte=last_3_month.year).count()

    last_6_month_order = order.filter(created_on__month__gte=last_6_month.month,
                                      created_on__year__gte=last_3_month.year).count()

    this_year = order.filter(created_on__year=today.year).count()

    data['today_order_qty'] = today_order_qty
    data['yesterday_order_qty'] = yesterday_order_qty
    data['this_week_order_qty'] = this_week_order_qty
    data['this_month_order_qty'] = this_month_order_qty

    data['last_3_month_order'] = last_3_month_order
    data['last_6_month_order'] = last_6_month_order
    data['this_year'] = this_year
    data['overall_order'] = order.count()

    data['today_order'] = today_order
    data['today_order_per'] = increase_decrease_per(today_order, yesterday_order)
    data['yesterday_order'] = yesterday_order
    data['yesterday_order_per'] = increase_decrease_per(yesterday_order, two_day_order)
    data['this_week'] = this_week_order
    data['this_week_per'] = increase_decrease_per(this_week_order, last_week_order)
    data['total_month'] = this_month_order
    data['total_month_per'] = increase_decrease_per(this_month_order, last_month_order)

    countries = models.Countries.objects.filter(is_active=True)
    transaction = []
    for country in countries:
        country_order = order.filter(address__country=country)
        today_revenue = country_order.filter(created_on__date=now().date()).aggregate(total=Sum("pay_amount"))['total']
        overall_revenue = country_order.filter().aggregate(total=Sum("pay_amount"))['total']
        yesterday_revenue = \
            country_order.filter(created_on__date=(datetime.now() - timedelta(days=1)).date()).aggregate(
                total=Sum("pay_amount"))[
                'total']
        this_week_revenue = \
            country_order.filter(created_on__week=int(now().strftime("%V"))).aggregate(total=Sum("pay_amount"))[
                'total']
        total_month_revenue = country_order.filter(created_on__month=today.month).aggregate(total=Sum("pay_amount"))[
            'total']
        last_3_month_revenue = \
            country_order.filter(created_on__month__gte=last_3_month.month).aggregate(total=Sum("pay_amount"))['total']

        transaction.append({"name": country.title, "currency_type": country.currency_type,
                            "today_revenue": today_revenue, "yesterday_revenue": yesterday_revenue,
                            "this_week_revenue": this_week_revenue, "total_month_revenue": total_month_revenue,
                            "last_3_month_revenue": last_3_month_revenue, "overall_revenue": overall_revenue})

    data['transaction'] = transaction
    data['products_obj'] = Products.objects.filter(id__in=[1, 2, 3, 4, 5], is_active=True)

    data['products_table'] = products_table

    data['transaction_per_day'] = list(
        transactions.filter(created_on__month=now().month, created_on__year=now().year).annotate(
            day=ExtractDay('created_on')).values('day').annotate(count=Count('id')).values('day', 'count'))

    data['last_30_days'] = order.filter(created_on__date__gte=datetime.now() - timedelta(days=30)).annotate(
        day=TruncDay('created_on')).values('day').annotate(total=Count('id'))

    return data
