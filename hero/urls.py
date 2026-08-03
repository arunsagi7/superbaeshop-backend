from django.urls import path, include
from rest_framework import routers
from . import views

router = routers.SimpleRouter()
router.register('hero', views.HeroVideoViewSet, basename='hero')

urlpatterns = router.urls
