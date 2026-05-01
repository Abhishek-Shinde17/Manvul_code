from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from .models import Order, OrderItem, OrderStatusLog
from store.models import Cart, CartItem, Coupon, CouponUsage
from accounts.models import Address, OTPVerification
from notifications.utils import notify, send_otp_email, send_order_email
import io

def get_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        sk = request.session.session_key
        cart, _ = Cart.objects.get_or_create(session_key=sk, user=None)
    return cart

@login_required
def checkout(request):
    cart = get_cart(request)
    if not cart.items.exists():
        messages.error(request, 'Your cart is empty.')
        return redirect('store:cart')
    addresses = request.user.addresses.all()
    coupon_id = request.session.get('coupon_id')
    coupon = None; coupon_discount = 0
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon_discount = coupon.calculate_discount(cart.total)
        except: pass
    subtotal = cart.total
    shipping = 0 if subtotal >= 999 else 99
    tax = round(subtotal * 18 / 100, 2)
    total = max(0, subtotal + shipping + tax - coupon_discount)
    loyalty_pts = request.user.loyalty_points
    max_loyalty_discount = min(loyalty_pts / 10, float(total) * 0.10)
    return render(request, 'orders/checkout.html', {
        'cart': cart, 'addresses': addresses, 'coupon': coupon,
        'subtotal': subtotal, 'shipping': shipping, 'tax': tax,
        'coupon_discount': coupon_discount, 'total': total,
        'loyalty_pts': loyalty_pts, 'max_loyalty_discount': max_loyalty_discount,
    })

@login_required
def place_order(request):
    if request.method != 'POST':
        return redirect('orders:checkout')
    cart = get_cart(request)
    if not cart.items.exists():
        messages.error(request, 'Cart is empty.'); return redirect('store:cart')

    addr_id = request.POST.get('address_id')
    use_loyalty = request.POST.get('use_loyalty') == 'on'
    payment_method = request.POST.get('payment_method', 'cod')

    if addr_id:
        addr = get_object_or_404(Address, id=addr_id, user=request.user)
        ship_name = addr.full_name; ship_phone = addr.phone
        ship_addr = addr.line1 + (f', {addr.line2}' if addr.line2 else '')
        ship_city = addr.city; ship_state = addr.state; ship_pin = addr.pincode
    else:
        ship_name = request.POST.get('full_name','')
        ship_phone = request.POST.get('phone','')
        ship_addr = request.POST.get('address','')
        ship_city = request.POST.get('city','')
        ship_state = request.POST.get('state','')
        ship_pin = request.POST.get('pincode','')

    coupon_id = request.session.get('coupon_id')
    coupon = None; coupon_discount = 0
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon_discount = coupon.calculate_discount(cart.total)
        except: pass

    # subtotal = cart.total
    # shipping = 0 if subtotal >= 999 else 99
    # tax = round(subtotal * 18 / 100, 2)
    # loyalty_discount = 0
    # if use_loyalty and request.user.loyalty_points > 0:
    #     loyalty_discount = min(request.user.loyalty_points / 10, float(subtotal) * 0.10)
    #     loyalty_discount = round(loyalty_discount, 2)
    # total = max(0, subtotal + shipping + tax - coupon_discount - loyalty_discount)

    from decimal import Decimal

    subtotal = cart.total  # already Decimal

    shipping = Decimal("0") if subtotal >= Decimal("999") else Decimal("99")

    tax = (subtotal * Decimal("0.18")).quantize(Decimal("0.01"))

    loyalty_discount = Decimal("0")

    if use_loyalty and request.user.loyalty_points > 0:
        raw_discount = min(
            Decimal(request.user.loyalty_points) / Decimal("10"),
            subtotal * Decimal("0.10")
        )
        loyalty_discount = raw_discount.quantize(Decimal("0.01"))

    coupon_discount = Decimal(coupon_discount)  # ensure this too!

    total = subtotal + shipping + tax - coupon_discount - loyalty_discount
    total = max(Decimal("0"), total)


    # Generate delivery OTP
    from accounts.models import OTPVerification
    import random, string
    delivery_otp = ''.join(random.choices(string.digits, k=6))

    order = Order.objects.create(
        user=request.user,
        shipping_name=ship_name, shipping_phone=ship_phone,
        shipping_address=ship_addr, shipping_city=ship_city,
        shipping_state=ship_state, shipping_pincode=ship_pin,
        subtotal=subtotal, shipping_charge=shipping, tax=tax,
        coupon_discount=coupon_discount, loyalty_discount=loyalty_discount,
        total=total, coupon=coupon,
        loyalty_points_used=int(loyalty_discount * 10),
        loyalty_points_earned=int(total // 100),
        payment_method=payment_method,
        payment_status='paid' if payment_method == 'online' else 'pending',
        status='confirmed',
        delivery_otp=delivery_otp,
        estimated_delivery=timezone.now().date() + timezone.timedelta(days=5),
    )
    order.invoice_number = f"INV-{order.order_number}"; order.save()

    for item in cart.items.all():
        OrderItem.objects.create(
            order=order, product=item.product, product_name=item.product.name,
            variant=item.variant, size=item.variant.size if item.variant else '',
            color=item.variant.color if item.variant else '',
            quantity=item.quantity, price=item.product.price,
        )
        item.product.stock = max(0, item.product.stock - item.quantity)
        item.product.sales_count += item.quantity
        item.product.save()

    OrderStatusLog.objects.create(order=order, status='confirmed', note='Order placed successfully', location='ManVault Warehouse')

    # Coupon usage
    if coupon:
        CouponUsage.objects.create(coupon=coupon, user=request.user, order_id=order.order_number, discount_given=coupon_discount)
        coupon.used_count += 1; coupon.save()
        if 'coupon_id' in request.session: del request.session['coupon_id']

    # Loyalty points
    if use_loyalty and loyalty_discount > 0:
        request.user.loyalty_points -= int(loyalty_discount * 10)
    request.user.loyalty_points += order.loyalty_points_earned
    request.user.save()

    cart.items.all().delete()

    # Notifications
    send_order_email(request.user, order, 'placed')
    # Send delivery OTP info
    send_otp_email(request.user, delivery_otp, f"delivery confirmation for order #{order.order_number}")
    notify(request.user, f'Order #{order.order_number} Confirmed! 🎉',
           f'Your order is confirmed. Total: ₹{total}. Delivery OTP will be sent when out for delivery.',
           'order', f'/orders/{order.order_number}/')

    messages.success(request, f'Order #{order.order_number} placed! 🎉')
    return redirect('orders:order_success', order_id=order.id)

@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/success.html', {'order': order})

@login_required
def order_list(request):
    status_filter = request.GET.get('status','')
    orders = Order.objects.filter(user=request.user)
    if status_filter: orders = orders.filter(status=status_filter)
    for order in orders:
        order.items_list = order.items.all()
    status_choices = [
        ("confirmed", "Confirmed"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    status_choices_ = [
    ("all", "All"),
    ("confirmed", "Confirmed"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ]
    return render(request, 'orders/order_list.html', {'orders': orders, 'status_filter': status_filter,'status_choices': status_choices,'status_choices_': status_choices_})

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    flow = [('confirmed','Confirmed','✅'),('processing','Processing','⚙️'),
            ('packed','Packed','📦'),('shipped','Shipped','🚚'),
            ('out_for_delivery','Out for Delivery','🛵'),('delivered','Delivered','🏠')]
    steps = []
    current = order.status
    reached = False
    for val, label, icon in flow:
        if val == current: reached = True
        steps.append({'val':val,'label':label,'icon':icon,'done': order.status_step >= [v for v,_,_ in flow].index(val)})
    return render(request, 'orders/order_detail.html', {'order': order, 'steps': steps})

@login_required
def track_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    flow = [('confirmed','Confirmed','✅'),('processing','Processing','⚙️'),
            ('packed','Packed','📦'),('shipped','Shipped','🚚'),
            ('out_for_delivery','Out for Delivery','🛵'),('delivered','Delivered','🏠')]
    steps = [{'val':v,'label':l,'icon':i,'done': order.status_step >= idx}
             for idx,(v,l,i) in enumerate(flow)]
    logs = order.logs.all()
    return render(request, 'orders/track_order.html', {'order': order, 'steps': steps, 'logs': logs})

@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['pending','confirmed','processing']:
        reason = request.POST.get('reason','Customer cancelled')
        order.status = 'cancelled'; order.save()
        OrderStatusLog.objects.create(order=order, status='cancelled', note=reason)
        # Refund loyalty points
        if order.loyalty_points_used > 0:
            request.user.loyalty_points += order.loyalty_points_used
            request.user.save()
        notify(request.user, f'Order #{order.order_number} Cancelled',
               f'Your order has been cancelled.', 'order', f'/orders/{order.order_number}/')
        messages.success(request, 'Order cancelled successfully.')
    else:
        messages.error(request, 'This order cannot be cancelled.')
    return redirect('orders:order_detail', order_number=order.order_number)

@login_required
def return_request(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'delivered':
        reason = request.POST.get('reason','')
        order.status = 'return_requested'; order.return_reason = reason; order.save()
        OrderStatusLog.objects.create(order=order, status='return_requested', note=reason)
        notify(request.user, f'Return Requested for #{order.order_number}',
               'Your return request has been received.', 'order', f'/orders/{order.order_number}/')
        messages.success(request, 'Return request submitted!')
    else:
        messages.error(request, 'Only delivered orders can be returned.')
    return redirect('orders:order_detail', order_number=order.order_number)

@login_required
def verify_delivery_otp(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if request.method == 'POST':
        entered = request.POST.get('otp','').strip()
        if entered == order.delivery_otp:
            order.delivery_otp_verified = True
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.payment_status = 'paid'
            order.save()
            OrderStatusLog.objects.create(order=order, status='delivered', note='Delivery confirmed via OTP', location=order.shipping_city)
            send_order_email(request.user, order, 'delivered')
            notify(request.user, f'Order #{order.order_number} Delivered! ✅',
                   f'Your order has been delivered. We hope you love your purchase!', 'delivery', f'/orders/{order.order_number}/')
            messages.success(request, '✅ Delivery confirmed! Thank you for shopping with ManVault.')
        else:
            messages.error(request, '❌ Incorrect OTP. Please try again.')
    return redirect('orders:order_detail', order_number=order.order_number)

@login_required
def download_invoice(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        # Header
        p.setFillColorRGB(0.78, 1, 0)
        p.rect(0, h-80, w, 80, fill=True, stroke=False)
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 22)
        p.drawString(2*cm, h-50, "ManVault")
        p.setFont("Helvetica", 10)
        p.drawString(2*cm, h-65, "Premium Men's Fashion")
        p.setFont("Helvetica-Bold", 14)
        p.drawRightString(w-2*cm, h-45, f"INVOICE")
        p.setFont("Helvetica", 10)
        p.drawRightString(w-2*cm, h-60, f"#{order.invoice_number}")
        p.drawRightString(w-2*cm, h-73, f"{order.created_at.strftime('%d %b %Y')}")
        # Order info
        p.setFillColorRGB(0.1, 0.1, 0.1)
        p.setFont("Helvetica-Bold", 11)
        p.drawString(2*cm, h-110, "Bill To:")
        p.setFont("Helvetica", 10)
        p.drawString(2*cm, h-125, order.shipping_name)
        p.drawString(2*cm, h-138, order.shipping_address)
        p.drawString(2*cm, h-151, f"{order.shipping_city}, {order.shipping_state} - {order.shipping_pincode}")
        p.drawString(2*cm, h-164, f"Phone: {order.shipping_phone}")
        # Items table header
        y = h-200
        p.setFillColorRGB(0.1,0.1,0.1)
        p.rect(2*cm, y-5, w-4*cm, 20, fill=True, stroke=False)
        p.setFillColorRGB(1,1,1)
        p.setFont("Helvetica-Bold", 10)
        p.drawString(2.2*cm, y+3, "Item")
        p.drawString(12*cm, y+3, "Qty")
        p.drawString(14*cm, y+3, "Price")
        p.drawString(16.5*cm, y+3, "Total")
        y -= 20
        p.setFillColorRGB(0.1,0.1,0.1)
        for item in order.items.all():
            p.setFont("Helvetica", 10)
            p.drawString(2.2*cm, y, item.product_name[:40])
            if item.size: p.drawString(2.2*cm, y-12, f"Size: {item.size}")
            p.drawString(12*cm, y, str(item.quantity))
            p.drawString(14*cm, y, f"Rs.{item.price}")
            p.drawString(16.5*cm, y, f"Rs.{item.subtotal}")
            y -= 30
            if y < 5*cm: p.showPage(); y = h-3*cm
        # Totals
        y -= 10
        p.line(2*cm, y, w-2*cm, y); y -= 20
        rows = [('Subtotal', f'Rs.{order.subtotal}'), ('Shipping', f'Rs.{order.shipping_charge}'), ('Tax (GST 18%)', f'Rs.{order.tax}')]
        if order.coupon_discount > 0: rows.append((f'Coupon ({order.coupon.code})', f'-Rs.{order.coupon_discount}'))
        if order.loyalty_discount > 0: rows.append(('Loyalty Points', f'-Rs.{order.loyalty_discount}'))
        for label, val in rows:
            p.setFont("Helvetica", 10)
            p.drawRightString(15*cm, y, label)
            p.drawRightString(w-2*cm, y, val)
            y -= 16
        y -= 5; p.line(13*cm, y, w-2*cm, y); y -= 16
        p.setFont("Helvetica-Bold", 13)
        p.drawRightString(15*cm, y, "TOTAL")
        p.drawRightString(w-2*cm, y, f"Rs.{order.total}")
        # Footer
        p.setFont("Helvetica", 9)
        p.setFillColorRGB(0.5,0.5,0.5)
        p.drawCentredString(w/2, 2*cm, "Thank you for shopping with ManVault! | manvault.com | support@manvault.com")
        p.save()
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="ManVault-Invoice-{order.order_number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Could not generate invoice: {e}')
        return redirect('orders:order_detail', order_number=order.order_number)
