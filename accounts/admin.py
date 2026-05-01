from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Address, OTPVerification

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username','email','first_name','last_name','phone','email_verified','loyalty_points','is_staff']
    fieldsets = UserAdmin.fieldsets + (('Extra', {'fields': ('phone','avatar','date_of_birth','gender','email_verified','loyalty_points')}),)

@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user','label','city','state','is_default']

@admin.register(OTPVerification)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user','otp_type','code','is_used','created_at','expires_at']
    list_filter = ['otp_type','is_used']
