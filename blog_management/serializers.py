from rest_framework import serializers

from . import models


class AuthorsSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Authors
        fields = ("id", "name", "description", "profile_pic")


class TagsSerializers(serializers.ModelSerializer):
    class Meta:
        model = models.Tags
        fields = ("id", "name")


class BlogSerializers(serializers.ModelSerializer):
    author = AuthorsSerializers()
    tag = TagsSerializers(many=True)

    class Meta:
        model = models.Blog
        fields = ("id", "title", "slug", "short_description", "date", "description", "image", "tag", "author",
                  "meta_keyword", "meta_description")
