from rest_framework import viewsets, mixins

from . import serializers, models


class BlogViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    serializer_class = serializers.BlogSerializers
    model = models.Blog

    def get_queryset(self):
        return self.model.objects.filter(is_active=True).order_by("-date")
