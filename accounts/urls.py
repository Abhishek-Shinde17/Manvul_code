from django.urls import path,include
from . import views
app_name = 'accounts'
urlpatterns = [
    
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-email/', views.verify_email, name='verify_email'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('address/add/', views.add_address, name='add_address'),
    path('address/<int:pk>/edit/', views.edit_address, name='edit_address'),
    path('address/<int:pk>/delete/', views.delete_address, name='delete_address'),
]
