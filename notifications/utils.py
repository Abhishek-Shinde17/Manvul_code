from .models import Notification
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def notify(user, title, message, notif_type='system', link=''):
    """Create an in-app notification for a user."""
    Notification.objects.create(
        user=user, title=title, message=message,
        notif_type=notif_type, link=link
    )


def send_otp_email(user, otp_code, purpose="verification"):
    """Send an OTP email to the user. Logs errors instead of silently swallowing them."""
    subject = f"ManVault — Your OTP is {otp_code}"

    # Plain-text version
    text_body = f"""Hi {user.first_name or user.username},

Your ManVault OTP for {purpose} is:

        {otp_code}

This OTP is valid for 10 minutes. Do not share it with anyone.

If you did not request this, please ignore this email.

— Team ManVault
"""

    # HTML version — looks great in email clients
    html_body = f"""
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#FFF8FA;font-family:Arial,sans-serif">
  <div style="max-width:480px;margin:40px auto;background:#fff;border-radius:16px;
              border:1.5px solid #FFCFDF;overflow:hidden">
    <!-- Header -->
    <div style="background:linear-gradient(90deg,#E8004D,#FF2D6B);padding:28px 32px;text-align:center">
      <div style="font-size:32px;margin-bottom:4px">👔</div>
      <div style="color:#fff;font-size:22px;font-weight:800;letter-spacing:1px">ManVault</div>
      <div style="color:rgba(255,255,255,.8);font-size:13px">Premium Men's Fashion</div>
    </div>
    <!-- Body -->
    <div style="padding:36px 32px;text-align:center">
      <p style="color:#7A4A5A;font-size:15px;margin-bottom:8px">
        Hi <strong style="color:#2D1A22">{user.first_name or user.username}</strong>,
      </p>
      <p style="color:#7A4A5A;font-size:14px;margin-bottom:28px">
        Your OTP for <strong style="color:#2D1A22">{purpose}</strong> is:
      </p>
      <!-- OTP Box -->
      <div style="background:#FFF0F4;border:2px dashed #FFADC8;border-radius:14px;
                  padding:24px;margin-bottom:28px;display:inline-block;min-width:200px">
        <div style="font-size:42px;font-weight:900;color:#E8004D;
                    letter-spacing:14px;font-family:monospace">
          {otp_code}
        </div>
      </div>
      <p style="color:#C4929F;font-size:13px;margin-bottom:6px">
        ⏱ Valid for <strong>10 minutes</strong>
      </p>
      <p style="color:#C4929F;font-size:12px">
        Do not share this OTP with anyone.
      </p>
    </div>
    <!-- Footer -->
    <div style="background:#FFF8FA;border-top:1px solid #FFCFDF;
                padding:18px 32px;text-align:center">
      <p style="color:#C4929F;font-size:12px;margin:0">
        If you did not request this, ignore this email.
        <br>© 2024 ManVault · support@manvault.com
      </p>
    </div>
  </div>
</body>
</html>
"""

    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()
        logger.info(f"OTP email sent to {user.email} for {purpose}")
    except Exception as e:
        # Log the real error — don't swallow it silently
        logger.error(f"Failed to send OTP email to {user.email}: {e}")
        # Re-raise so the view can show an error message to the user
        raise


def send_order_email(user, order, event):
    """Send an order status email to the user."""
    events = {
        'placed': (
            f'Order Confirmed — #{order.order_number} 🎉',
            f'Your order #{order.order_number} has been placed successfully!\n'
            f'Total: ₹{order.total} | Payment: {order.get_payment_method_display()}\n'
            f'Estimated delivery: {order.estimated_delivery}\n\n'
            f'Your delivery OTP is: {order.delivery_otp}\n'
            f'Share this OTP with the delivery person to confirm receipt.'
        ),
        'shipped': (
            f'Order Shipped 🚚 — #{order.order_number}',
            f'Your order #{order.order_number} is on its way!\n'
            f'Tracking: {order.tracking_number} | Courier: {order.courier_name}'
        ),
        'out_for_delivery': (
            f'Out for Delivery Today 📦 — #{order.order_number}',
            f'Your order #{order.order_number} will be delivered today.\n\n'
            f'Delivery OTP: {order.delivery_otp}\n'
            f'Share this with the delivery person to confirm receipt.'
        ),
        'delivered': (
            f'Delivered ✅ — #{order.order_number}',
            f'Your order #{order.order_number} has been delivered!\n'
            f'Thank you for shopping with ManVault.'
        ),
        'cancelled': (
            f'Order Cancelled — #{order.order_number}',
            f'Your order #{order.order_number} has been cancelled.\n'
            f'If you paid online, your refund will be processed in 5-7 business days.'
        ),
    }
    if event not in events:
        return

    subject, body = events[event]
    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send order email to {user.email} for event={event}: {e}")

    notify(user, subject, body, notif_type='order', link=f'/orders/{order.order_number}/')