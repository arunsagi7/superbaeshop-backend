import json
import re

import requests
from django.utils.timezone import now

from categories.utils import int_to_country
from orders_management.models import OrderStatus, Orders
from others.models import ShipmentLogin


def shipment_login():
    try:
        login_details = ShipmentLogin.objects.get(pk=1)
    except ShipmentLogin.DoesNotExist:
        return None
    
    login_url = "https://apiv2.shiprocket.in/v1/external/auth/login"
    payload = {"email": login_details.username, "password": login_details.password}
    headers = {
        'Content-Type': 'application/json'
    }

    login_response = requests.request("POST", login_url, headers=headers, data=json.dumps(payload))
    if login_response.status_code == 200:
        login_details.token = login_response.json()['token']
        login_details.save()


def calculating_delivery_charges(country, delivery_postcode, weight, cod=0, pickup_postcode='600085'):
    try:
        login_details = ShipmentLogin.objects.get(pk=1)
        token = login_details.token
        url = """https://apiv2.shiprocket.in/v1/external/courier/serviceability/?pickup_postcode={pickup_postcode}&delivery_postcode={delivery_postcode}&weight={weight}&cod={cod}&mode=Surface""".format(
            delivery_postcode=delivery_postcode, pickup_postcode=pickup_postcode, weight=weight, cod=cod)

        payload = {}
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer  {token}'.format(token=token)
        }

        response = requests.request("GET", url, headers=headers, data=payload)

        if response.status_code == 200:
            order_result = response.json()

            recommended_courier_company_id = order_result['data']['recommended_courier_company_id']

            price = [x for x in order_result['data']['available_courier_companies'] if
                     x['courier_company_id'] == recommended_courier_company_id]
            return price[0]['rate']
    except ShipmentLogin.DoesNotExist:
        pass

    return country.shipping_fee


def order_shipment():
    try:
        login_details = ShipmentLogin.objects.get(pk=1)
    except ShipmentLogin.DoesNotExist:
        return
    
    token = login_details.token
    url = "https://apiv2.shiprocket.in/v1/external/orders?per_page=4000&from=2019-01-01&to={}".format(
        now().today().strftime("%Y-%m-%d"))
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {token}'.format(token=token)
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    order_missing = []
    status_missing = []

    if response.status_code == 200:
        order_result = response.json()
        for order_json in order_result['data']:
            print(order_json['channel_order_id'])
            status = OrderStatus.objects.filter(name=order_json['status']).first()
            if status:
                order = None
                try:
                    order = Orders.objects.get(tracking_client_id=order_json['channel_order_id'])
                except:
                    order_id = re.findall(r'S&B-[\d{4}]+-[\d]+', order_json['channel_order_id'])
                    if order_id:
                        order = Orders.objects.filter(tracking_client_id=order_id[0]).first()

                if order:
                    print(order)
                    order.status = status
                    if "shipments" in order_json:
                        print(order_json['shipments'][0]['awb'])
                        order.awb_code = order_json['shipments'][0]['awb']
                    order.save()
                else:
                    order_missing.append(order_json['channel_order_id'])
            else:
                status_missing.append(order_json['status'])

    elif response.status_code == 401:
        shipment_login()


def update_tracking_link(obj):
    try:
        login_details = ShipmentLogin.objects.get(pk=1)
    except ShipmentLogin.DoesNotExist:
        return
    
    token = login_details.token
    url = "https://apiv2.shiprocket.in/v1/external/courier/track/awb/{code}".format(code=obj.awb_code)
    payload = {}
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer {token}'.format(token=token)
    }

    response = requests.request("GET", url, headers=headers, data=payload)

    if response.status_code == 200:
        order_result = response.json()
        obj.track_url = order_result['tracking_data']['track_url']
        obj.save()
    elif response.status_code == 401:
        shipment_login()