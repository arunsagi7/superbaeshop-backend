from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r'^login/$', views.LoginView.as_view(), name='login_api'),
    url(r'^logout/$', views.LogoutView.as_view(), name='logout_api'),
    url(r'^dashboard/$', views.DashboardStatusView.as_view(), name='dashboard_api'),
    url(r'^menu/$', views.AdminMenuView.as_view(), name='admin_menu'),
    url(r'^orders/$', views.OrdersViewSet.as_view(), name='orders_api'),
    path('orders/status/<int:pk>/', views.OrdersStatusViewSet.as_view(), name='order_status_update'),
    path('users/', views.UserProfileView.as_view(), name='user_list'),
    path('affiliates/', views.AffiliateView.as_view(), name='affiliate_list'),
    path('cart-user/', views.CartUserView.as_view(), name='cart_user_list'),
]
