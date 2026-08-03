from django.urls import path
from rest_framework import routers

from . import views

router = routers.SimpleRouter()

router.register("", views.MasterCategoriesViewSet, basename="master_categories")
router.register("categories", views.CategoriesViewSet, basename="categories")

urlpatterns = [
    path('homepage-sections/', views.HomepageSectionView.as_view(), name='homepage-sections'),
    path('hero-banners/', views.HeroBannerView.as_view(), name='hero-banners'),
    path('countries/', views.CountriesView.as_view(), name='countries'),
] + router.urls
