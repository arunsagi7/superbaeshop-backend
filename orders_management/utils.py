import csv
from datetime import date, timedelta

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import F
from django.http import HttpResponse
from django.template import loader
from django.utils.timezone import now
from pyfcm import FCMNotification
from rest_framework import exceptions

from authentication.models import Token
from authentication.utils import SendEmailViewMixin, send_email
from cart_management.utils import offer_calculation
from . import models
from space_and_beauty import constants

YOUR_API_KEY = "rzp_live_TBLuE5IctyVSgR"
YOUR_API_SECRET = "QExjCdL2Li1Eiy9wqJ51PvEZ"


def push_notification(_type, orders):
    push_service = FCMNotification(
        api_key="AAAAPKY-2Gc:APA91bH4n8k01y_XeeHTsDhcLuMD8DmPwdC_CzNNZIhuqPzwsTyZEbFqwoLW2jn4HU1iAiD-4ouMb60Loq0863ojy"
                "CX88ODV0c7OQZSxivX3HOA7BdF3YhN7SDmDCR-cZKwz22PE9v24")

    token = Token.objects.filter(user__is_staff=True)
    if token:
        registration_ids = [x.device_token for x in token]
        data_message = {
            "type": _type,
            "title": "New {}({}) has proceed".format("Transaction" if _type == 2 else "Order",
                                                     orders.tracking_client_id),
            "description": "{}, {}, {}, {}".format(orders.name, orders.phone, orders.email,
                                                   orders.payment_type),
        }

        result = push_service.notify_multiple_devices(registration_ids=registration_ids, data_message=data_message)


def str2bool(value):
    return str(value).lower() in ("yes", "true", "t", "1")


def __generate_order_id():
    sku = models.Orders.objects.latest("id").id if models.Orders.objects.last() else 0
    order_id = "ORDER_{}".format('{0:08}'.format(sku + 1))
    return order_id


def id_to_cart_user(user, product, qty):
    product_obj = models.Products.objects.get(id=product)
    user.my_cart.create(product=product_obj, quantity=qty)
    return True


def calculate_amount(user, order, country, offer=None, is_wallet=None, delivery_charge=0):
    total_amount = 0
    coupon_amount = 0
    cod_charge = 0
    shipping_fee = 0
    quantity_count = 0
    total_gst = 0

    if not user.my_cart.all():
        raise exceptions.ValidationError({"non_field_error": [constants.CART_IS_EMPTY]})

    if order.payment_type == "COD":
        cod_charge = country.cod_charge

    cart_offer = offer_calculation(user.my_cart.all())

    for item in user.my_cart.all():

        product_price = item.product.product_country.get(country=country)
        if product_price:
            if item.product.stock_qty < item.quantity:
                raise exceptions.ValidationError({"non_field_errors": [constants.STOCK_EXISTS_CART_ITEM]})

            order_item = {"order": order, "product": item.product, "product_sku": item.product.sku,
                          "currency": country,
                          "color": item.color_code,
                          "quantity": item.quantity, "unit_price": product_price.selling_price}

            try:
                if cart_offer:
                    discount_cart = next(x for x in cart_offer["cart_id"] if x["id"] == item.id)
                else:
                    discount_cart = None
            except StopIteration:
                discount_cart = None

            if discount_cart:
                order_item['offer_title'] = discount_cart['offer']['title']
                order_item['offer_amount'] = discount_cart['discount']
                amount = round(product_price.selling_price * item.quantity, 2) - discount_cart['discount']
                total_amount += amount
                order_item['gst'] = round(((amount / 100) * 12), 2)

            elif item.is_offer:
                selling_price = round(product_price.selling_price * 0.8, 2)
                order_item['offer_title'] = "Flat 20% Offer, Flash Sales"
                order_item['offer_amount'] = round(product_price.selling_price - selling_price, 2)
                amount = round(selling_price * item.quantity, 2)
                total_amount += amount

                order_item['gst'] = round(((amount / 100) * 12), 2)

            else:
                selling_price = product_price.selling_price
                amount = round(selling_price * item.quantity, 2)
                order_item['gst'] = round(((amount / 100) * 12), 2)
                total_amount += amount

            quantity_count += item.quantity
            models.OrderItems.objects.create(**order_item)

    if is_wallet:
        if user.user_points > quantity_count * 100:
            point = quantity_count * 100
        else:
            point = user.user_points

        coupon_amount = round(point * country.redeem_point_cash, 2)

    elif offer:
        coupon_amount = round((total_amount / 100) * offer.payout, 2)

    if delivery_charge:
        shipping_fee += delivery_charge
    else:
        shipping_fee += country.shipping_fee

    total_gst = round((total_amount / 100) * 12, 2)

    total_amount = (total_amount + cod_charge + shipping_fee + total_gst)
    pay_amount = round(round(total_amount - coupon_amount, 2), 2)

    return {"total_amount": round(total_amount, 2), "cod_charge": cod_charge,
            "pay_amount": pay_amount, "coupon_amount": coupon_amount,
            "other_charge": 0,
            "total_gst": total_gst,
            "shipping_charge": shipping_fee, "razor_pay": int(pay_amount * 100)}


def generate_cod_order(user, address, country, payment_type, offer=None):
    amount = calculate_amount(user, country, offer)

    order_id = __generate_order_id()

    order = models.Orders.objects.create(user=user, address=address, total_amount=amount['total_amount'],
                                         payment_type=payment_type, tracking_client_id=order_id, offer=offer,
                                         pay_amount=amount['pay_amount'], shipping_charge=amount['shipping_charge'],
                                         cod_charge=amount['total_cod_charge'],
                                         coupon_amount=amount['coupon_amount'])

    for item in user.my_cart.all():
        price = item.product.product_country.get(country=country)

        models.OrderItems.objects.create(order=order, product=item.product, product_sku=item.product.sku,
                                         quantity=item.quantity, currency=country, unit_price=price.selling_price,
                                         cod_charge=price.cod_charge)

    user.my_cart.all().delete()
    return order


def int_to_order(order_id):
    try:
        return models.Orders.objects.get(id=order_id)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": ["{} is not a valid object's id".format(order_id)]})


def int_payment_id(order_id):
    try:
        return models.Orders.objects.get(transaction_id=order_id)
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_errors": ["{} is not a valid object's id".format(order_id)]})


def download_shipping():
    response = HttpResponse(content_type='text/csv')

    response['Content-Disposition'] = 'attachment; filename=order_shipping_{}.csv'.format(now().strftime("%d_%m_%Y"))
    writer = csv.writer(response)

    csv_headers = ("*Order Id", "Order Date as dd-mm-yyyy hh:MM", "*Channel", "*Payment Method(COD/Prepaid)",
                   "*Customer First Name", "*Customer Last Name", "*Email", "*Customer Mobile",
                   "*Shipping Address Line 1",
                   "*Shipping Address Line 2", "*Shipping Address Country", "*Shipping Address State",
                   "*Shipping Address City",
                   "*Shipping Address Postcode", "Billing Address Line 1", "Billing Address Line 2",
                   "Billing Address Country",
                   "Billing Address State", "Billing Address City", "Billing Address Postcode", "*Master SKU",
                   "*Product Name", "*Product Quantity",
                   "Tax %", "*Selling Price(Per Unit Item, Inclusive of Tax)", "Discount(Per Unit Item)",
                   "Shipping Charges(Per Order)",
                   "COD Charges(Per Order)", "Gift Wrap Charges(Per Order)", "Total Discount (Per Order)",
                   "*Length (cm)", "*Breadth (cm)",
                   "*Height (cm)", "Weight Of Shipment(kg)", "Send Notification(True/False)", "Comment", "HSN Code",
                   "Pickup Location Id", "Reseller Name", "Company Name", "Ewaybill No", "Customer Alternate Mobile")

    writer.writerow(csv_headers)
    yesterday = date.today() - timedelta(days=0)
    for item in models.OrderItems.objects.filter(order__is_success=True, order__created_on__date__lte=yesterday,
                                                 order__status=1):
        address_1 = "{}, {}".format(item.order.address.door_no, item.order.address.street_address)
        address_2 = "{}, {}".format(item.order.address.locality, "Landmark: {}".format(
            item.order.address.landmark) if item.order.address.landmark else "")
        country = item.order.address.country.title
        state = item.order.address.state
        city = item.order.address.city
        code = item.order.address.postal_code
        if item.product.id == 1 or item.order.order_items.filter(product=1):
            length = "50"
            breadth = "30"
            height = "7.5"
            weight = "3.5"
        else:
            length = "27"
            breadth = "20"
            height = "6.5"
            weight = "1.4"

        coupon_amount = item.order.coupon_amount + item.order.discount_amount()

        unit_price = item.unit_price + item.gst

        tax = round((item.gst / item.unit_price) * 100)

        row_list = [item.order.tracking_client_id, item.order.created_on.strftime("%d-%m-%Y %H:%M"), "MANUAL",
                    "COD" if item.order.payment_type == "COD" else "Prepaid", item.order.name, item.order.name,
                    item.order.email, item.order.phone, address_1, address_2, country, state, city, code, address_1,
                    address_2, country, state, city, code, item.product_sku, item.product.title, item.quantity, tax,
                    unit_price, "", item.order.shipping_charge, item.order.cod_charge, "",
                    coupon_amount, length, breadth, height, weight, "True", "", "", "", "", "", "",
                    item.order.alt_phone]
        writer.writerow(row_list)
    return response


def my_send_email():
    queryset = models.Orders.objects.filter(status__in=[31, 28, 27, 19, 18, 12, 3, 1], is_success=True).order_by(
        "-created_on")
    bcc_email = [o.email for o in queryset]

    subject = loader.render_to_string("dely_txt.txt", {})
    subject = ''.join(subject.splitlines())

    html_body = loader.render_to_string("dely_html.html", {})

    requests.post(
        "https://api.mailgun.net/v3/mail.scoremaxneetschool.com/messages",
        auth=("api", "key-8ddd4368287cf32d15ab2c5f8b1d4efd"),
        data={"from": "SpaceAndBeauty<noreply@spaceandbeauty.com>",
              "to": ["official@spaceandbeauty.com"], "subject": subject,
              "bcc": bcc_email,
              "html": html_body})
    print(bcc_email)


def update_order_price(order):
    total_price = 0
    total_gst = 0
    coupon_amount = 0

    already_paid_amount = order.pay_amount

    for item in order.order_items.all():
        price = round(item.unit_price * item.quantity, 2) - item.offer_amount
        total_price += price
        total_gst += round(price * 0.12, 2)

    total_amount = total_price + order.cod_charge + order.shipping_charge
    order.total_amount = total_amount + total_gst
    order.total_gst = total_gst

    if order.coupon:
        coupon_amount = round((order.total_amount / 100) * order.coupon.payout, 2)
        order.coupon_amount = coupon_amount

    order.pay_amount = round(round(order.total_amount - coupon_amount, 2), 2)

    if order.payment_status and order.pay_amount < already_paid_amount:
        order.refund_amount = round(already_paid_amount - order.pay_amount, 2)
        order.is_amount_refunded = False

    order.save()
