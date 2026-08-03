from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register('dashboard', views.DashBoardViewSet, basename="dashboard")
router.register('', views.AffiliatesViewSet, basename="affiliates")

urlpatterns = [
              ] + router.urls
