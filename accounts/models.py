from django.contrib.auth.models import AbstractUser
from django.db import models
import pyotp, random, string
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    phone = models.CharField(max_length=15, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M','Male'),('F','Female'),('O','Other')], blank=True)
    email_verified = models.BooleanField(default=False)
    is_google_account = models.BooleanField(default=False)
    loyalty_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.email or self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class Address(models.Model):
    ADDRESS_TYPES = [('home','Home'),('work','Work'),('other','Other')]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    full_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.label} - {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

class OTPVerification(models.Model):
    OTP_TYPES = [
        ('email_verify', 'Email Verification'),
        ('delivery', 'Delivery OTP'),
        ('password_reset', 'Password Reset'),
        ('login', 'Login OTP'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    code = models.CharField(max_length=6)
    order_id = models.CharField(max_length=20, blank=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.code = ''.join(random.choices(string.digits, k=6))
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.user} - {self.otp_type} - {self.code}"
