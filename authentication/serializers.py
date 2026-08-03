from django.contrib.auth import get_user_model
from rest_framework import serializers

from categories.models import Countries
from . import utils

User = get_user_model()


class RegistrationSerializer(serializers.ModelSerializer, utils.SendOneTimePassword):
    username = serializers.CharField()
    token = serializers.CharField(read_only=True, required=False)
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    email = serializers.EmailField()
    user_key = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "token", "user_key")


class ActivationSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    otp = serializers.IntegerField(min_value=000000, max_value=999999)
    client = serializers.CharField(max_length=254)

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField()
    email = serializers.EmailField()
    country = serializers.PrimaryKeyRelatedField(queryset=Countries.objects.filter(is_active=True))

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class ObtainAuthenticationSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    username = serializers.CharField()
    client = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class UpdateMobileNumberSerializer(serializers.Serializer):
    otp = serializers.IntegerField()
    username = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass


class DeviceTokenSerializer(serializers.Serializer):
    client = serializers.CharField()
    device_token = serializers.CharField()

    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass
