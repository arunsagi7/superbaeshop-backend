from django.core.exceptions import ObjectDoesNotExist
from rest_framework import exceptions

from product_management import models


def int_to_product(pk):
    try:
        return models.Products.objects.get(pk=pk)
    except ObjectDoesNotExist:
        raise exceptions.NotFound()


def slug_to_product(slug):
    try:
        return models.Products.objects.get(slug=slug)
    except ObjectDoesNotExist:
        raise exceptions.NotFound()
