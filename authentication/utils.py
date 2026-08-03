import binascii
import os
import random
import urllib
from urllib.request import urlretrieve

import requests
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from pyfcm import FCMNotification
from rest_framework import exceptions

from space_and_beauty import constants
from . import models

User = get_user_model()


def random_digits(digits):
    lower = 10 ** (digits - 1)
    upper = 10 ** digits - 1
    return random.randint(lower, upper)


class SendOneTimePassword(object):

    def __init__(self):
        self.sms_template = None
        self.sms_context = None

    def send_verification_otp(self, user, template_id, message=None, mobile_number=None, sms_template=None,
                              sms_context=None):
        mobiles = int(user.username)
        if sms_template:
            message = loader.render_to_string(sms_template, sms_context)
        elif self.sms_template:
            message = loader.render_to_string(self.sms_template, self.sms_context)
        self.send_message(mobiles, message, mobile_number, template_id)

    @staticmethod
    def send_message(mobiles, message, mobile_number, template_id):
        mobile_number = mobile_number if mobile_number else mobiles
        values = {
            'authkey': "336881ABHNSvSgsR5f1c1623P1",
            'mobiles': mobile_number if mobile_number else int(mobiles),
            'message': message,
            'sender': "BPVPSB",
            'route': "4",
            'DLT_TE_ID': template_id
        }
        url = "http://api.msg91.com/api/sendhttp.php"
        try:
            post_data = urllib.parse.urlencode(values).encode('utf-8')
            req = urllib.request.Request(url, post_data)
            urllib.request.urlopen(req)
            print("sms Send")
        except Exception as e:
            print(e)


def get_or_create_token(user, client):
    token, created = models.Token.objects.get_or_create(client=client, user=user,
                                                        defaults={'user': user, 'client': client,
                                                                  'key': binascii.hexlify(os.urandom(20)).decode()})
    return token


class ActionViewMixin(object):
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return self.action(serializer)
        else:
            raise exceptions.ValidationError(serializer.errors)

    def put(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            return self.action(serializer)
        else:
            raise exceptions.ValidationError(serializer.errors)


def get_download_image(local_path, image_url):
    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    urlretrieve(image_url, local_path)
    return True


def int_to_user_object(user_id):
    try:
        return User.objects.get(pk=int(user_id))
    except ObjectDoesNotExist:
        raise exceptions.ValidationError({"non_field_error": [constants.INVALID_USER_OBJECT]})


def push_notification(notification, user):
    service = FCMNotification(api_key="AAAA4tGgzpk:APA91bFwOuz_AhgihhTaSRx0VI_P7zzwRa8x-BaXcbItU2y91YIexh6BMBUwFxwAy"
                                      "CtrkuSvY1LP9ITYXzeqAdVLjOSQHB8Vv3aBbMkhg19CegKH6r_EHmH2ukM-cf1kUmNVYDEm2HGl")

    token = models.Token.objects.filter(user=user)
    if token:
        registration_ids = [x.device_token for x in token]
        data_message = {
            "type": notification.type,
            "title": notification.title,
            "description": notification.description,
            "image": notification.image.url if notification.image else None,
            "id": notification.id
        }

        service.notify_multiple_devices(registration_ids=registration_ids, data_message=data_message)


class PushNotification(object):
    def __init__(self):
        self.admin_api_key = "AAAA4tGgzpk:APA91bFwOuz_AhgihhTaSRx0VI_P7zzwRa8x" \
                             "-BaXcbItU2y91YIexh6BMBUwFxwAyCtrkuSvY1LP9ITYXzeqAdVLjOSQHB8Vv3aBbMkhg19CegKH6r_EHmH2ukM" \
                             "-cf1kUmNVYDEm2HGl "

    def user_define_admin_push_notification(self, user, message):
        service = FCMNotification(self.admin_api_key)

        token = models.Token.objects.filter(user__in=user, device_token__isnull=False)
        if token:
            registration_ids = [x.device_token for x in token]
            service.notify_multiple_devices(registration_ids=registration_ids, data_message=message)


def send_email(to_email, context, subject_template_name,
               plain_body_template_name=None, html_body_template_name=None):
    assert plain_body_template_name or html_body_template_name
    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())

    html_body = loader.render_to_string(html_body_template_name, context)

    requests.post(
        "https://api.mailgun.net/v3/mail.scoremaxneetschool.com/messages",
        auth=("api", "key-8ddd4368287cf32d15ab2c5f8b1d4efd"),
        data={"from": "SpaceAndBeauty<noreply@spaceandbeauty.com>",
              "to": [to_email], "subject": subject,
              "html": html_body})
    print("email sent.")


def encode_uid(pk):
    try:
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        return urlsafe_base64_encode(force_bytes(pk)).decode()
    except ImportError:
        from django.utils.http import int_to_base36
        return int_to_base36(pk)


def decode_uid(pk):
    try:
        from django.utils.http import urlsafe_base64_decode
        from django.utils.encoding import force_text
        return force_text(urlsafe_base64_decode(pk))
    except ImportError:
        from django.utils.http import base36_to_int
        return base36_to_int(pk)


class SendEmailViewMixin(object):
    token_generator = None
    subject_template_name = None
    plain_body_template_name = None
    html_body_template_name = None

    def __init__(self):
        self.request = None

    def send_email(self, to_email, context):
        send_email(to_email, context, **self.get_send_email_extras())

    def get_send_email_extras(self):
        return {
            'subject_template_name': self.get_subject_template_name(),
            'plain_body_template_name': self.get_plain_body_template_name(),
            'html_body_template_name': self.get_html_body_template_name(),
        }

    def get_subject_template_name(self):
        return self.subject_template_name

    def get_plain_body_template_name(self):
        return self.plain_body_template_name

    def get_html_body_template_name(self):
        return self.html_body_template_name

    def get_send_email_kwargs(self, user):
        return {
            'to_email': user.email,
            'context': self.get_email_context(user),
        }

    def get_email_context(self, user):
        uid = user.pk
        return {
            'user': user,
            'uid': uid,
            "token": ""
        }
