from django.db import models
from accounts.models import User

class Notification(models.Model):
    NOTIF_TYPES = [
        ('order','Order Update'),
        ('offer','Special Offer'),
        ('delivery','Delivery'),
        ('otp','OTP'),
        ('system','System'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES, default='system')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    link = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ['-created_at']
    def __str__(self): return f"{self.user} - {self.title}"
