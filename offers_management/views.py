from django.shortcuts import render
from rest_framework import viewsets, exceptions, response

from . import utils, serializers


class ValidateCouponView(viewsets.GenericViewSet):
    """
    use this endpoint to validate coupon
    """

    def create(self, request):
        if not ("coupon_code" in request.data and request.data['coupon_code']):
            raise exceptions.ValidationError({"non_field_errors": ["coupon_code is Required"]})

        code = utils.code_coupon(request.data['coupon_code'])
        serializer = serializers.CouponSerializers(code, context={"request": self.request}).data

        return response.Response(serializer)
