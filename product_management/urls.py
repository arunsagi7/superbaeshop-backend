from django.urls import path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()
router.register('', views.ProductsViewSet, basename="products")

urlpatterns = [
                  path("by_ids/", views.ProductsByIdsView.as_view(), name="products_by_ids"),
                  path("upload-product/", views.ProductUploadView.as_view(), name="upload_product"),
              ] + router.urls
