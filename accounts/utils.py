from rest_framework import exceptions

from accounts import models
from accounts.models import UserPointsHistory


def int_to_address(id, user):
    try:
        return models.Address.objects.get(user=user, id=id)
    except:
        raise exceptions.NotFound()


def user_point_history(order, point, is_credit):
    user = order.user
    if is_credit:
        user.user_points -= point
        user.used_points += point
        wallet_credit = False
    else:
        user.user_points += point
        user.total_points += point
        wallet_credit = True

    user.save()
    description = "{}".format(order.tracking_client_id)
    UserPointsHistory.objects.create(user=user, point=point, pre_point=0,
                                     description=description,
                                     is_credit=wallet_credit)
    return True
