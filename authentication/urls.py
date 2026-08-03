from django.urls import path

from . import views

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup_api'),
    path('login/', views.LoginView.as_view(), name='login_api'),
    path('logout/', views.LogoutView.as_view(), name='logout_api'),
    path('verify-otp/', views.ObtainAuthenticationView.as_view(), name='obtain-token'),
    path('resend-otp/', views.ResendOTPViews.as_view(), name='resend-otp'),
    path('update/device-token/', views.FcmTokenUpdateView.as_view(), name='update_device_token'),

]
