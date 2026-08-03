from rest_framework import serializers
from .models import HeroVideo, HeroVideoProduct
from product_management.serializers import ListProductSerializers


class HeroVideoProductSerializer(serializers.ModelSerializer):
    product = ListProductSerializers(read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = HeroVideoProduct
        fields = ('id', 'product', 'image')

    def get_image(self, obj):
        if obj.product and obj.product.thumbnail_image:
            return obj.product.thumbnail_image.url
        return None


class HeroVideoSerializer(serializers.ModelSerializer):
    products = HeroVideoProductSerializer(many=True, read_only=True)

    class Meta:
        model = HeroVideo
        fields = ('id', 'title', 'video', 'order', 'is_active', 'products')
