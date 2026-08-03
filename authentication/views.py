import datetime
from threading import Thread

import django.contrib.auth.signals
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Q
from rest_framework import generics, response, permissions, status, exceptions

from accounts.models import UserProfile
from accounts.serializers import UserProfileSerializers
from authentication import utils, serializers, models, signals, settings
from categories.utils import int_to_country
from space_and_beauty import constants


class SignUpView(generics.GenericAPIView, utils.ActionViewMixin, utils.SendOneTimePassword,
                 utils.PushNotification, utils.SendEmailViewMixin):
    """
        use this endpoint to request login an user (obtain authentication token).
    """
    serializer_class = serializers.SignUpSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_template = "otp_send_sms.txt"
        self.subject_template_name = 'otp_email_subject.txt'
        self.html_body_template_name = 'otp_email_body.html'

    @transaction.atomic()
    def action(self, serializer):
        user = self.validate_user(serializer)

        if not hasattr(user, "userprofile"):
            raise exceptions.ValidationError({"non_field_errors": [constants.ALREADY_MEMBER_SPACEANDBEAUTY]})

        self.sms_context = {"user": user, "otp": user.userprofile.otp}
        now = datetime.datetime.now()

        if not user.userprofile.otp or user.userprofile.otp_expired.time() < now.time():
            user.userprofile.otp = utils.random_digits(6)

        if not user.userprofile.otp_expired:
            user.userprofile.otp_expired = now + datetime.timedelta(minutes=30)

        user.userprofile.save()

        Thread(target=self.send_verification_otp, args=(user,), kwargs={"template_id": "1307162572077585049"}).start()

        kwargs = self.get_send_email_kwargs(user)
        Thread(target=self.send_email, args=(kwargs['to_email'], kwargs['context'],)).start()

        data = {"user": user.id,
                "data": "An OTP has been sent to {} and +{}-{}".format(user.email,
                                                                       user.userprofile.country.dial_code,
                                                                       user.username)}
        return response.Response(data=data)

    def get_email_context(self, user):
        context = super(SignUpView, self).get_email_context(user)
        context['user'] = user
        context['url'] = settings.get('ACTIVATION_URL', 3).format(**context)
        return context

    def validate_user(self, serializer):
        try:
            user = models.User.objects.get(username=serializer.data["username"])
            if user and user.is_active:
                raise exceptions.ValidationError({"username": [constants.USERNAME_ALREADY_EXISTS]})
            else:
                user.email = serializer.data['email']
                user.save()
                country = int_to_country(serializer.data['country'])
                user.userprofile.country = country
                user.userprofile.save()
        except ObjectDoesNotExist:
            if models.User.objects.filter(email=serializer.data['email']):
                raise exceptions.ValidationError({"email": [constants.EMAIL_ALREADY_EXISTS]})

            user = models.User.objects.create(username=serializer.data["username"], email=serializer.data['email'])
            country = int_to_country(serializer.data['country'])
            UserProfile.objects.create(user=user, country=country)
            signals.user_registered.send(sender=self.__class__, user=user, request=self.request)
        return user


class LoginView(generics.GenericAPIView, utils.ActionViewMixin, utils.SendOneTimePassword,
                utils.PushNotification, utils.SendEmailViewMixin):
    """
        use this endpoint to request login an user (obtain authentication token).
    """
    serializer_class = serializers.LoginSerializer

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sms_template = "otp_send_sms.txt"
        self.subject_template_name = 'sign_otp_email_subject.txt'
        self.html_body_template_name = 'signin_otp_email_body.html'

    @transaction.atomic()
    def action(self, serializer):
        user = self.validate_user(serializer)

        self.sms_context = {"user": user, "otp": user.userprofile.otp}
        now = datetime.datetime.now()

        if not user.userprofile.otp or user.userprofile.otp_expired.time() < now.time():
            user.userprofile.otp = utils.random_digits(6)
            # user.userprofile.otp = 123456

        if not user.userprofile.otp_expired:
            user.userprofile.otp_expired = now + datetime.timedelta(minutes=30)

        user.userprofile.save()

        Thread(target=self.send_verification_otp, args=(user,), kwargs={"template_id": "1307162572077585049"}).start()
        kwargs = self.get_send_email_kwargs(user)
        Thread(target=self.send_email, args=(kwargs['to_email'], kwargs['context'],)).start()

        data = {"user": user.id,
                "data": "An OTP has been sent to {} and +{}-{}".format(user.email,
                                                                       user.userprofile.country.dial_code,
                                                                       user.username)}
        return response.Response(data=data)

    @staticmethod
    def validate_user(serializer):
        try:
            user = models.User.objects.get(
                Q(username=serializer.data["username"]) | Q(email=serializer.data["username"]))
        except ObjectDoesNotExist:
            raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_USERNAME]})
        return user

    def get_email_context(self, user):
        context = super(LoginView, self).get_email_context(user)
        context['user'] = user
        context['url'] = settings.get('ACTIVATION_URL', 3).format(**context)
        return context


class ObtainAuthenticationView(generics.GenericAPIView, utils.ActionViewMixin):
    """
        use this endpoint to obtain authentication token and enter into application.
    """
    serializer_class = serializers.ObtainAuthenticationSerializer

    @transaction.atomic()
    def action(self, serializer):
        user = self.get_user(serializer)
        if user.userprofile.otp != int(serializer.data['otp']):
            raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_OTP_ERROR]})
        user.userprofile.otp = None
        user.userprofile.otp_expired = None
        user.userprofile.save()
        user.userprofile.token = utils.get_or_create_token(user, serializer.data["client"]).key
        data = UserProfileSerializers(user.userprofile, context={'request': self.request}).data
        django.contrib.auth.signals.user_logged_in.send(sender=user.__class__, request=self.request, user=user)
        return response.Response(data=data)

    @staticmethod
    def get_user(serializer):
        try:
            return models.User.objects.get(Q(username=serializer.data["username"]) |
                                           Q(email=serializer.data["username"]))
        except ObjectDoesNotExist:
            raise exceptions.ValidationError({"non_field_errors": [constants.INVALID_USERNAME]})


class ResendOTPViews(generics.GenericAPIView, utils.SendOneTimePassword):
    """
    use this endpoint to resend user OTP.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.SMS_MESSAGE = "otp_send_sms.txt"
        self.sms_template = 'otp_send_sms.txt'

    def post(self, request):

        if not ("user_id" in request.data and request.data['user_id']):
            raise exceptions.ValidationError({"non_field_errors":
                                                  [constants.REQUIRED_FIELD_ERROR.format("user_id")]})

        user = utils.int_to_user_object(request.data['user_id'])
        now = datetime.datetime.now()
        if not user.userprofile.otp_expired:
            user.userprofile.otp_expired = now + datetime.timedelta(minutes=30)

        if not user.userprofile.otp or user.userprofile.otp_expired.time() < now.time():
            user.userprofile.otp = utils.random_digits(6)
            # user.userprofile.otp = 123456

        user.userprofile.otp_expired = now + datetime.timedelta(minutes=30)
        user.userprofile.save()

        self.sms_context = {"user": user, "otp": user.userprofile.otp}

        Thread(target=self.send_verification_otp, args=(user,), kwargs={"template_id": "1307162572077585049"}).start()

        data = {"user": user.id,
                "data": "An OTP has been sent to {} and +{}-{}".format(user.email,
                                                                       user.userprofile.country.dial_code,
                                                                       user.username)}
        return response.Response(data=data)


class LogoutView(generics.GenericAPIView):
    """
    use this endpoint to logout an user (remove user authentication token).
    """
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(self, request):
        if request.auth:
            request.auth.delete()
            django.contrib.auth.signals.user_logged_out.send(sender=self.request.user.__class__, request=request,
                                                             user=request.user)
        return response.Response(status=status.HTTP_200_OK)


class FcmTokenUpdateView(generics.GenericAPIView):
    """
    use this endpoint to update fcm token
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    def post(self, request):
        serializer = serializers.DeviceTokenSerializer(data=self.request.data)
        if not serializer.is_valid():
            raise exceptions.ValidationError(serializer.errors)

        request.auth.device_token = request.data['device_token']
        request.auth.save()

        return response.Response(serializer.data)
