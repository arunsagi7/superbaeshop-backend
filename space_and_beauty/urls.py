"""space_and_beauty URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve

from categories.admin import my_admin_site

urlpatterns = [
    path('', my_admin_site.urls),
    path("django-admin/", admin.site.urls),
    path('master-values/', include('categories.urls')),
    path('summernote/', include('django_summernote.urls')),
    path('admin-api/', include('administration.urls')),
    path('affiliates/', include('affiliate_management.urls')),
    path('users/', include('accounts.urls')),
    path('cart/', include('cart_management.urls')),
    path('offers/', include('offers_management.urls')),
    path('products/', include('product_management.urls')),
    path('orders/', include('orders_management.urls')),
    path("others-api/", include("others.urls")),
    path('blog/', include('blog_management.urls')),
    path('auth/', include('authentication.urls')),
    path('api/', include('hero.urls')),
    path('homebanner/', include('hero.urls')),
] + [url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
     url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATICFILES_DIRS})]
