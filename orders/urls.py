from django.urls import path
from . import views
app_name = 'orders'
urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('place/', views.place_order, name='place_order'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),
    path('my-orders/', views.order_list, name='order_list'),
    path('<str:order_number>/', views.order_detail, name='order_detail'),
    path('<str:order_number>/track/', views.track_order, name='track_order'),
    path('cancel/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('return/<int:order_id>/', views.return_request, name='return_request'),
    path('verify-delivery/<int:order_id>/', views.verify_delivery_otp, name='verify_delivery'),
    path('<str:order_number>/invoice/', views.download_invoice, name='download_invoice'),
]
