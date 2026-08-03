import locale

from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions

from categories import models
from space_and_beauty import constants


def int_to_country(pk):
    try:
        return models.Countries.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OBJECT_ERROR.format(pk)]})


def float_to_rupee(value=0):
    if value is None:
        value = 0
    # locale.setlocale(locale.LC_MONETARY, 'en_IN')
    return round(value, 2)


def int_to_super_category(pk):
    try:
        return models.SuperCategories.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OBJECT_ERROR.format(pk)]})


def int_to_category(pk):
    try:
        return models.Categories.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OBJECT_ERROR.format(pk)]})


def int_to_sub_categories(pk):
    try:
        return models.SubCategories.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OBJECT_ERROR.format(pk)]})
