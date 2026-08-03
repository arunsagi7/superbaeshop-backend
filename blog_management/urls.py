from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register('', views.BlogViewSet, basename="blog")

urlpatterns = [
              ] + router.urls
