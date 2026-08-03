from django.db.models import Sum


def revenue_order_calculation(order, dict_value):
    count = order.filter(**dict_value).count()
    revenue = order.filter(**dict_value).aggregate(total=Sum("pay_amount"))['total']
    if revenue is None:
        revenue = 0
    return count, revenue
