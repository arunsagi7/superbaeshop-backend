from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register('newsletter', views.NewslettersView, basename="newsletter")
router.register('html-content', views.MasterHtmlContentViewSet, basename="master_html_api")

urlpatterns = [
              ] + router.urls
