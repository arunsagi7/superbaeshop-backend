from rest_framework import routers

from . import views
from django.urls import path

router = routers.SimpleRouter()
router.register('guest', views.GuestCartViewSet, basename="guest-cart")
router.register('', views.CartViewSet, basename="cart")

urlpatterns = [
                  path("remainder-mail", views.CartRemainderEmailView.as_view(), )
              ] + router.urls
