from django.db import transaction
from rest_framework import serializers, exceptions

from accounts import models
from categories.serializers import CountriesSerializers
from categories.models import Countries


class UserPointsHistorySerializers(serializers.ModelSerializer):
    class Meta:
        model = models.UserPointsHistory
        fields = ("id", "point", "pre_point", "is_credit", "created_on", "description")


class AddressSerializer(serializers.ModelSerializer):
    country_id = serializers.PrimaryKeyRelatedField(queryset=Countries.objects.all(), write_only=True)
    country = CountriesSerializers(read_only=True)

    class Meta:
        model = models.Address
        fields = ("id", "door_no", "street_address", "city", "landmark", "address_type",
                  "country", "postal_code", "country_id", "state", "locality")

    def create(self, validated_data):
        if not hasattr(self.context['request'].user, "userprofile"):
            raise exceptions.NotFound()
        validated_data['user'] = self.context['request'].user.userprofile
        validated_data['country'] = validated_data.pop("country_id")

        return self.Meta.model.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.door_no = validated_data.get("door_no", instance.door_no)
        instance.street_address = validated_data.get("street_address", instance.street_address)
        instance.city = validated_data.get("city", instance.city)
        instance.landmark = validated_data.get("landmark", instance.landmark)
        instance.address_type = validated_data.get("address_type", instance.address_type)
        instance.country = validated_data.get("country", instance.country)
        instance.postal_code = validated_data.get("postal_code", instance.postal_code)

        instance.save()

        return instance


class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = ("id", "first_name", "last_name", "username", "email")


class UserProfileSerializers(serializers.ModelSerializer):
    user = UserSerializers(read_only=True)
    token = serializers.CharField(required=False)
    user_address = AddressSerializer(many=True, read_only=True)
    user_points_history = UserPointsHistorySerializers(many=True, read_only=True)
    country = CountriesSerializers(read_only=True)

    class Meta:
        model = models.UserProfile
        fields = ("user", "profile_pic", "gender", "user_points", "token", "user_address",
                  "user_points_history", "used_points", "total_points", "country")

    @transaction.atomic()
    def update(self, instance, validated_data):
        request = self.context['request']
        instance.profile_pic = validated_data.get("profile_pic", instance.profile_pic)
        instance.gender = validated_data.get("gender", instance.gender)

        instance.user.first_name = request.data.get("first_name", instance.user.first_name)
        instance.user.last_name = request.data.get("last_name", instance.user.last_name)
        instance.user.email = request.data.get("email", instance.user.email)

        instance.save()
        instance.user.save()

        return instance