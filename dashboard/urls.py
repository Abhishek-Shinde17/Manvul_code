from django.urls import path
from . import views
app_name = 'dashboard'
urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('analytics/', views.analytics, name='analytics'),
    # Products
    path('products/', views.product_list, name='products'),
    path('products/new/', views.product_form, name='product_new'),
    path('products/<int:pk>/edit/', views.product_form, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete, name='product_delete'),
    path('products/<int:pk>/toggle/', views.product_toggle, name='product_toggle'),
    # Orders
    path('orders/', views.order_list, name='orders'),
    path('orders/<str:order_number>/', views.order_detail, name='order_detail'),
    # Customers
    path('customers/', views.customer_list, name='customers'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    # Categories
    path('categories/', views.category_list, name='categories'),
    path('categories/new/', views.category_form, name='category_new'),
    path('categories/<int:pk>/edit/', views.category_form, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    # Coupons
    path('coupons/', views.coupon_list, name='coupons'),
    path('coupons/new/', views.coupon_form, name='coupon_new'),
    path('coupons/<int:pk>/edit/', views.coupon_form, name='coupon_edit'),
    path('coupons/<int:pk>/delete/', views.coupon_delete, name='coupon_delete'),
    # Offers
    path('offers/', views.offer_list, name='offers'),
    path('offers/new/', views.offer_form, name='offer_new'),
    path('offers/<int:pk>/edit/', views.offer_form, name='offer_edit'),
    path('offers/<int:pk>/delete/', views.offer_delete, name='offer_delete'),
]
