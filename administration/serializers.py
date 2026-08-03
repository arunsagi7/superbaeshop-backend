from rest_framework import serializers

from accounts.models import UserProfile
from authentication.utils import User
from cart_management.serializers import CartSerializers
from categories.serializers import CountriesSerializers
from orders_management.models import Orders
from product_management.serializers import TitleSerializer


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
    client = serializers.CharField()

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class UserSerializer(serializers.ModelSerializer):
    token = serializers.CharField(required=False)

    class Meta:
        model = User
        fields = ("id", "first_name", "last_name", "email", "is_staff", "is_superuser", "token", "date_joined",
                  "last_login", "username")


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orders
        fields = ("id", "is_read")


class UserProfileSerializers(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    country = CountriesSerializers(read_only=True)
    my_cart = CartSerializers(read_only=True, many=True)

    class Meta:
        model = UserProfile
        fields = ("user", "profile_pic", "otp", "user_points", "used_points", "total_points", "country", "my_cart")
