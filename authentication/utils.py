import binascii
import os
import random
import urllib
from urllib.request import urlretrieve

import requests
import re
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.template import loader
from pyfcm import FCMNotification
from rest_framework import exceptions
from . import models
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


def _render_otp_email(otp_code: str) -> str:
    """Render the OTP email using the rich HTML template.
    The template file is `templates/otp_email.html` and expects a variable `otp`.
    """
    return loader.render_to_string("otp_email.html", {"OTP": otp_code})


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
        # Previously this method sent OTP via SMS using the phone number stored in the username.
        # We now send the OTP via email using Resend.com. Prefer the user's registered email.
        mobiles = int(user.username)
        if sms_template:
            message = loader.render_to_string(sms_template, sms_context)
        elif self.sms_template:
            message = loader.render_to_string(
                self.sms_template, self.sms_context)
        # Determine recipient email – require a valid email address
        recipient_email = getattr(user, "email", None)
        if not recipient_email:
            raise ValueError(
                "User does not have a valid email for OTP delivery")
        # Simple email validation (must contain '@' and a domain)
        if "@" not in recipient_email or "." not in recipient_email.split("@")[-1]:
            raise ValueError("Invalid email format for OTP delivery")
        self.send_message(mobiles, message, recipient_email, template_id)

    @staticmethod
    def send_message(mobiles, message, mobile_number, template_id):
        # Resend.com email OTP delivery (using the provided API key)
        # The OTP is sent as an email; mobile_number is interpreted as the recipient email.
        api_key = os.getenv("RESEND_API_KEY")
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        # Helper to validate a minimal email format

        def _is_valid_email(addr):
            return isinstance(addr, str) and "@" in addr and "." in addr.split("@")[-1]

        # Extract numeric OTP from any surrounding text
        def _extract_otp(text: str) -> str:
            """Return the first sequence of 4‑6 digits found in *text*.
            If no such sequence exists, the original *text* is returned.
            """
            match = re.search(r"\b\d{4,6}\b", text)
            return match.group(0) if match else text

        # Determine proper recipient email address
        if _is_valid_email(mobile_number):
            recipient = mobile_number
        else:
            # Fallback to a placeholder or raise error – cannot send invalid email
            raise ValueError("Invalid recipient email for OTP delivery")

        payload = {
            "from": "SuperBae <noreply@contact.superbae.shop>",
            "to": [recipient],
            "subject": "Your SuperBae Verification Code",
            "text": _extract_otp(message),
            "html": _render_otp_email(_extract_otp(message)),
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            print("OTP email sent via Resend.com")
        except Exception as e:
            print("Failed to send OTP via Resend:", e)


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
        raise exceptions.ValidationError(
            {"non_field_error": [constants.INVALID_USER_OBJECT]})


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

        service.notify_multiple_devices(
            registration_ids=registration_ids, data_message=data_message)


class PushNotification(object):
    def __init__(self):
        self.admin_api_key = "AAAA4tGgzpk:APA91bFwOuz_AhgihhTaSRx0VI_P7zzwRa8x" \
                             "-BaXcbItU2y91YIexh6BMBUwFxwAyCtrkuSvY1LP9ITYXzeqAdVLjOSQHB8Vv3aBbMkhg19CegKH6r_EHmH2ukM" \
                             "-cf1kUmNVYDEm2HGl "

    def user_define_admin_push_notification(self, user, message):
        service = FCMNotification(self.admin_api_key)

        token = models.Token.objects.filter(
            user__in=user, device_token__isnull=False)
        if token:
            registration_ids = [x.device_token for x in token]
            service.notify_multiple_devices(
                registration_ids=registration_ids, data_message=message)


def send_email(to_email, context, subject_template_name,
               plain_body_template_name=None, html_body_template_name=None):
    assert plain_body_template_name or html_body_template_name
    subject = loader.render_to_string(subject_template_name, context)
    subject = ''.join(subject.splitlines())

    html_body = loader.render_to_string(html_body_template_name, context)

    requests.post(
        "https://api.mailgun.net/v3/mail.scoremaxneetschool.com/messages",
        auth=("api", "key-8ddd4368287cf32d15ab2c5f8b1d4efd"),
        data={"from": "SuperBae <noreply@contact.superbae.shop>",
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
