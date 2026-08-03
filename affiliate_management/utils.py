import random
import string

from rest_framework import exceptions

from space_and_beauty import constants
from . import models


def generate(size=4):
    code = ''.join(random.choice(string.ascii_uppercase) for i in range(size))

    return code


def create_offers(name, code):
    title = "{} Affiliate Offer Code 6%".format(name)
    offer_code = "{}".format(code)
    offer = models.Coupon.objects.create(title=title, description=title, payout=6, offer_code=offer_code)

    return offer


def int_to_affiliates(user_id):
    try:
        return models.Affiliates.objects.get(id=user_id)
    except:
        raise exceptions.NotFound()


def code_to_affiliates(referral_code):
    try:
        return models.Affiliates.objects.get(offer__offer_code=referral_code)
    except:
        raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OBJECT_ERROR.format(referral_code)]})


def affiliate_price_calculation(order):
    total_price = 0

    for item in order.order_items.all():
        price = float(item.quantity * item.unit_price)
        total_price += round(float((price / 100) * item.product.affiliate_percentage))

    affiliate = order.coupon.affiliate_offer

    affiliate.wallet_amount += round(float(total_price))
    affiliate.total_amount += round(float(total_price))
    affiliate.save()

    models.WalletHistory.objects.create(user=affiliate, currency=order.address.country,
                                        amount=total_price,
                                        description="Your earnings from {} order".format(order.tracking_client_id),
                                        is_credit=True)

    if hasattr(affiliate, "referral_user"):
        if affiliate.referral_user.all().first():
            super_affiliate = affiliate.referral_user.all().first().referred_by

            referral_amount = round((float(total_price) / 100 * 20), 2)
            super_affiliate.wallet_amount += referral_amount
            super_affiliate.total_amount += referral_amount

            super_affiliate.save()
            description = "Your earnings from your sub-affiliate - {} - {} order".format(referral_amount,
                                                                                         affiliate.user.get_full_name())
            models.WalletHistory.objects.create(user=super_affiliate, currency=order.address.country,
                                                amount=referral_amount, description=description, is_credit=True)

    return True
