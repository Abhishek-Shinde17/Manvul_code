from django.contrib import admin
from .models import (Category, Brand, Product, ProductImage, ProductVariant,
                     Review, Cart, CartItem, Wishlist, Coupon, CouponUsage, SpecialOffer)

class ProductImageInline(admin.TabularInline):
    model = ProductImage; extra = 1
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant; extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name','category','price','stock','badge','is_active','is_featured','rating']
    list_filter = ['category','brand','badge','is_active','is_featured']
    search_fields = ['name']
    list_editable = ['is_active','is_featured','price','stock']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductVariantInline]

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name','slug','is_active']
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Brand)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code','discount_type','value','min_order','used_count','max_uses','is_active','valid_to']
    list_editable = ['is_active']

@admin.register(SpecialOffer)
class SpecialOfferAdmin(admin.ModelAdmin):
    list_display = ['name','offer_type','discount_percent','valid_from','valid_to','is_active']
    list_editable = ['is_active']

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product','user','rating','verified_purchase','created_at']
