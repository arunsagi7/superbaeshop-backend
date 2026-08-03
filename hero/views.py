from rest_framework import viewsets, permissions
from .models import HeroVideo
from .serializers import HeroVideoSerializer

class HeroVideoViewSet(viewsets.ReadOnlyModelViewSet):
    """Public endpoint – returns ordered active hero videos with linked products."""
    permission_classes = (permissions.AllowAny,)
    queryset = HeroVideo.objects.filter(is_active=True)
    serializer_class = HeroVideoSerializer
