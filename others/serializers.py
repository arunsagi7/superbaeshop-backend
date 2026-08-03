from rest_framework import serializers

from others import models


class MasterHtmlSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.MasterHtml
        fields = ("id", "title", "content")


class NewslettersSerializers(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = models.Newsletters
        fields = ("email",)

    def create(self, validated_data):
        return self.Meta.model.objects.get_or_create(**validated_data)[0]
