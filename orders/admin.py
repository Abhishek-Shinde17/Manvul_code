from django.contrib import admin
from .models import Order, OrderItem, OrderStatusLog

class OrderItemInline(admin.TabularInline):
    model = OrderItem; extra = 0
class StatusLogInline(admin.TabularInline):
    model = OrderStatusLog; extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number','user','status','payment_method','payment_status','total','created_at']
    list_filter = ['status','payment_method','payment_status']
    search_fields = ['order_number','user__email','shipping_name']
    list_editable = ['status','payment_status']
    inlines = [OrderItemInline, StatusLogInline]
