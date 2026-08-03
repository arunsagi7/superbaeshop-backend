from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions

from . import models
from space_and_beauty import constants


def int_to_offer_code(code):
    try:
        return models.Coupon.objects.get(offer_code=code, is_active=True)
    except ObjectDoesNotExist:
        raise exceptions.NotFound()


def code_coupon(code, validate=True):
    try:
        return models.Coupon.objects.get(offer_code=code, is_active=True)
    except ObjectDoesNotExist:
        if validate:
            raise exceptions.ValidationError({"coupon_code": [constants.INVALID_COUPON_ERROR]})
        return None


def exits_code_coupon(code):
    try:
        models.Coupon.objects.get(offer_code=code, is_active=True)
        raise exceptions.ValidationError({"coupon_code": [constants.INVALID_COUPON_EXITS_ERROR]})
    except ObjectDoesNotExist:
        return None
