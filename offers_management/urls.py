from rest_framework import routers

from . import views

router = routers.SimpleRouter()

router.register("validate", views.ValidateCouponView, basename="validate-coupon")

urlpatterns = [

              ] + router.urls
