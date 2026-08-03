from rest_framework import routers

from . import views

router = routers.SimpleRouter()
# Register sub-resources before the generic user profile route to avoid catch‑all matching
router.register('address', views.UserAddressViewSet, basename="user_address")
router.register('my-points', views.UserPointsHistoryViewSet, basename="my_points_history")
router.register('', views.UserProfileViewSet, basename="users")

urlpatterns = [] + router.urls
