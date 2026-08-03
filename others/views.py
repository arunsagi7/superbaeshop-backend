from rest_framework import viewsets, mixins

from . import models, serializers


class NewslettersView(viewsets.GenericViewSet, mixins.CreateModelMixin):
    model = models.Newsletters
    serializer_class = serializers.NewslettersSerializers

    def get_queryset(self):
        return self.model.objects.all()


class MasterHtmlContentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin):
    """

    """
    queryset = models.MasterHtml
    serializer_class = serializers.MasterHtmlSerializers
