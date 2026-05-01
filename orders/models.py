from django.db import models
from accounts.models import User, Address
from store.models import Product, ProductVariant, Coupon, SpecialOffer
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending','Pending'),
        ('confirmed','Confirmed'),
        ('processing','Processing'),
        ('packed','Packed'),
        ('shipped','Shipped'),
        ('out_for_delivery','Out for Delivery'),
        ('delivered','Delivered'),
        ('cancelled','Cancelled'),
        ('return_requested','Return Requested'),
        ('returned','Returned'),
        ('refund_initiated','Refund Initiated'),
        ('refunded','Refunded'),
    ]
    PAYMENT_METHODS = [('cod','Cash on Delivery'),('online','Online Payment'),('wallet','Wallet')]
    PAYMENT_STATUS = [('pending','Pending'),('paid','Paid'),('failed','Failed'),('refunded','Refunded')]

    order_number = models.CharField(max_length=20, unique=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)

    shipping_name = models.CharField(max_length=100)
    shipping_phone = models.CharField(max_length=15)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_pincode = models.CharField(max_length=10)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_charge = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    coupon_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    offer_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    loyalty_discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    loyalty_points_used = models.PositiveIntegerField(default=0)
    loyalty_points_earned = models.PositiveIntegerField(default=0)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cod')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_id = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    tracking_number = models.CharField(max_length=50, blank=True)
    courier_name = models.CharField(max_length=100, blank=True)
    estimated_delivery = models.DateField(null=True, blank=True)
    delivery_otp = models.CharField(max_length=6, blank=True)
    delivery_otp_verified = models.BooleanField(default=False)
    return_reason = models.TextField(blank=True)
    invoice_number = models.CharField(max_length=20, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta: ordering = ['-created_at']

    def __str__(self): return self.order_number

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = 'MV' + str(uuid.uuid4().hex[:8]).upper()
        if not self.invoice_number and self.pk:
            self.invoice_number = f"INV-{self.order_number}"
        super().save(*args, **kwargs)

    @property
    def total_discount(self):
        return self.coupon_discount + self.offer_discount + self.loyalty_discount

    @property
    def status_step(self):
        flow = ['confirmed','processing','packed','shipped','out_for_delivery','delivered']
        try: return flow.index(self.status)
        except ValueError: return -1

    @property
    def status_percent(self):
        flow = ['confirmed','processing','packed','shipped','out_for_delivery','delivered']
        try:
            idx = flow.index(self.status)
            return int((idx / (len(flow)-1)) * 100)
        except: return 0

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.CharField(max_length=20, blank=True)
    color = models.CharField(max_length=50, blank=True)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    is_returned = models.BooleanField(default=False)
    return_reason = models.TextField(blank=True)

    @property
    def subtotal(self):
        return (self.price - self.discount_applied) * self.quantity

class OrderStatusLog(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='logs')
    status = models.CharField(max_length=25)
    note = models.TextField(blank=True)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['created_at']
