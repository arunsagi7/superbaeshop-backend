from django.urls import path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register('checkout', views.CheckoutViewSet, basename="orders")
router.register('', views.OrdersViewSet, basename="my_orders")

urlpatterns = [
                  path("payment-success/", views.PaymentSuccess.as_view(), name='payment_success'),
                  path("influencer/create-order/", views.InfluencerOrderViewSet.as_view(), name='payment_success'),
                  path("cod-confirm/<int:pk>/", views.CODConfirmationView.as_view(), name='cod_confirm'),
                  path("order-to-email/<int:pk>/", views.OrderToEmailView.as_view(), name='order_to_email'),
                  path("order-tracking/<int:pk>/", views.GetOrderTrackingLink.as_view(), name='order_tracking'),
                  path("calculate-delivery/", views.CalculateDeliveryAmountView.as_view(),
                       name='calculate_delivery'),
              ] + router.urls
