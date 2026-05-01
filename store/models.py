from django.db import models
from django.utils.text import slugify
from django.utils import timezone
from accounts.models import User

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    icon = models.CharField(max_length=10, default='👕')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Brand(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    def __str__(self): return self.name

class Product(models.Model):
    BADGE_CHOICES = [('','None'),('new','NEW'),('hot','HOT'),('sale','SALE'),('trending','TRENDING')]
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    material = models.CharField(max_length=200, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock = models.PositiveIntegerField(default=0)
    badge = models.CharField(max_length=20, choices=BADGE_CHOICES, blank=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0)
    review_count = models.PositiveIntegerField(default=0)
    sales_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return self.name
    def save(self, *args, **kwargs):
        if not self.slug: self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    @property
    def discount_percent(self):
        if self.original_price and self.original_price > self.price:
            return int(((self.original_price - self.price) / self.original_price) * 100)
        return 0
    @property
    def main_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    class Meta: ordering = ['order']

class ProductVariant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=20)
    color = models.CharField(max_length=50, blank=True)
    color_hex = models.CharField(max_length=7, blank=True)
    stock = models.PositiveIntegerField(default=0)
    extra_price = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    def __str__(self): return f"{self.product.name} - {self.size} {self.color}"

class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(i,i) for i in range(1,6)])
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField()
    verified_purchase = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    images = models.ImageField(upload_to='reviews/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ['product','user']
        ordering = ['-created_at']

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='cart')
    session_key = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())
    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey(ProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)
    @property
    def subtotal(self):
        return self.product.price * self.quantity

class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# ─── Coupon & Offer Models ─────────────────────────────────────────────────────
class Coupon(models.Model):
    DISCOUNT_TYPES = [('flat','Flat ₹'),('percent','Percent %')]
    code = models.CharField(max_length=20, unique=True)
    description = models.CharField(max_length=200, blank=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPES, default='flat')
    value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    max_discount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Max discount cap for percent type")
    max_uses = models.PositiveIntegerField(default=100)
    max_uses_per_user = models.PositiveIntegerField(default=1)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    applicable_categories = models.ManyToManyField(Category, blank=True)
    applicable_products = models.ManyToManyField(Product, blank=True)
    first_order_only = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.code

    def calculate_discount(self, cart_total):
        if self.discount_type == 'flat':
            return min(self.value, cart_total)
        else:
            disc = (cart_total * self.value) / 100
            if self.max_discount:
                disc = min(disc, self.max_discount)
            return disc

    def is_valid_for_user(self, user, cart_total):
        now = timezone.now()
        if not self.is_active: return False, "Coupon is inactive."
        if now < self.valid_from: return False, "Coupon not yet active."
        if now > self.valid_to: return False, "Coupon has expired."
        if self.used_count >= self.max_uses: return False, "Coupon usage limit reached."
        if cart_total < self.min_order: return False, f"Minimum order ₹{self.min_order} required."
        if user.is_authenticated:
            user_uses = CouponUsage.objects.filter(user=user, coupon=self).count()
            if user_uses >= self.max_uses_per_user: return False, "You've already used this coupon."
            if self.first_order_only:
                from orders.models import Order
                if Order.objects.filter(user=user, status__in=['confirmed','delivered']).exists():
                    return False, "This coupon is for first orders only."
        return True, "Valid"

class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order_id = models.CharField(max_length=20)
    used_at = models.DateTimeField(auto_now_add=True)
    discount_given = models.DecimalField(max_digits=8, decimal_places=2)

class SpecialOffer(models.Model):
    OFFER_TYPES = [
        ('bxgy','Buy X Get Y Free'),
        ('bundle','Bundle Discount'),
        ('flash','Flash Sale'),
        ('loyalty','Loyalty Points Bonus'),
        ('seasonal','Seasonal Offer'),
    ]
    name = models.CharField(max_length=200)
    offer_type = models.CharField(max_length=20, choices=OFFER_TYPES)
    description = models.TextField()
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount_flat = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    buy_quantity = models.PositiveIntegerField(default=1, help_text="For BxGy: buy X")
    get_quantity = models.PositiveIntegerField(default=1, help_text="For BxGy: get Y free")
    applicable_products = models.ManyToManyField(Product, blank=True)
    applicable_categories = models.ManyToManyField(Category, blank=True)
    loyalty_points_multiplier = models.DecimalField(max_digits=4, decimal_places=1, default=1)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    banner_image = models.ImageField(upload_to='offers/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): return self.name

    @property
    def is_live(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_to

    @property
    def time_remaining(self):
        if timezone.now() < self.valid_to:
            delta = self.valid_to - timezone.now()
            h, rem = divmod(int(delta.total_seconds()), 3600)
            m = rem // 60
            return f"{h}h {m}m"
        return "Expired"
