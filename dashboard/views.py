from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from datetime import timedelta
import json

from store.models import Product, Category, Brand, Coupon, SpecialOffer, ProductImage, ProductVariant
from orders.models import Order, OrderStatusLog
from accounts.models import User
from notifications.utils import notify, send_order_email

@staff_member_required
def dashboard_home(request):
    today = timezone.now().date()
    orders_today = Order.objects.filter(created_at__date=today).count()
    revenue_today = Order.objects.filter(created_at__date=today).aggregate(s=Sum('total'))['s'] or 0
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(s=Sum('total'))['s'] or 0
    total_products = Product.objects.filter(is_active=True).count()
    total_customers = User.objects.filter(is_staff=False).count()
    pending_orders = Order.objects.filter(status__in=['pending','confirmed','processing']).count()
    low_stock = Product.objects.filter(stock__lte=5, is_active=True).count()

    # 7-day revenue chart
    days = [(today - timedelta(days=i)) for i in range(6,-1,-1)]
    revenue_data = []
    for d in days:
        rev = Order.objects.filter(created_at__date=d).aggregate(s=Sum('total'))['s'] or 0
        revenue_data.append(float(rev))
    labels = [d.strftime('%d %b') for d in days]

    # Category distribution
    cat_data = Category.objects.annotate(cnt=Count('products')).values('name','cnt').order_by('-cnt')[:6]

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]
    return render(request, 'dashboard/home.html', {
        'orders_today': orders_today, 'revenue_today': revenue_today,
        'total_orders': total_orders, 'total_revenue': total_revenue,
        'total_products': total_products, 'total_customers': total_customers,
        'pending_orders': pending_orders, 'low_stock': low_stock,
        'revenue_labels': json.dumps(labels),
        'revenue_data': json.dumps(revenue_data),
        'cat_data': json.dumps(list(cat_data)),
        'recent_orders': recent_orders,
    })

@staff_member_required
def analytics(request):
    # Monthly revenue (12 months)
    months = []
    for i in range(11,-1,-1):
        d = timezone.now() - timedelta(days=i*30)
        rev = Order.objects.filter(created_at__year=d.year, created_at__month=d.month).aggregate(s=Sum('total'))['s'] or 0
        months.append({'label': d.strftime('%b %Y'), 'value': float(rev)})
    top_products = Product.objects.order_by('-sales_count')[:10]
    top_cats = Category.objects.annotate(rev=Sum('products__orderitem__price')).order_by('-rev')[:6]
    status_dist = Order.objects.values('status').annotate(c=Count('id'))
    return render(request, 'dashboard/analytics.html', {
        'months': json.dumps(months),
        'top_products': top_products,
        'top_cats': top_cats,
        'status_dist': list(status_dist),
    })

# ── Products ──────────────────────────────────────────────────────────────────
@staff_member_required
def product_list(request):
    q = request.GET.get('q','')
    products = Product.objects.select_related('category','brand').all()
    if q: products = products.filter(name__icontains=q)
    cat_filter = request.GET.get('cat','')
    if cat_filter: products = products.filter(category__slug=cat_filter)
    return render(request, 'dashboard/products/list.html', {
        'products': products, 'q': q,
        'categories': Category.objects.all(), 'cat_filter': cat_filter,
    })

@staff_member_required
def product_form(request, pk=None):
    from .forms import ProductForm

    product = get_object_or_404(Product, pk=pk) if pk else None
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    print(request.FILES.getlist('images'))
    if form.is_valid():
        p = form.save()

        files = request.FILES.getlist('images')
        
        if files:
            
            has_primary = p.images.filter(is_primary=True).exists()
            start_order = p.images.count()

            for i, img in enumerate(files):
                ProductImage.objects.create(
                    product=p,
                    image=img,
                    is_primary=(not has_primary and i == 0),
                    order=start_order + i
                )

        messages.success(request, f'Product {"updated" if pk else "created"}!')
        return redirect('dashboard:products')

    return render(request, 'dashboard/products/form.html', {
        'form': form,
        'product': product
    })

@staff_member_required
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, 'Product deleted.')
        return redirect('dashboard:products')
    return render(request, 'dashboard/products/confirm_delete.html', {'product': product})

@staff_member_required
def product_toggle(request, pk):
    p = get_object_or_404(Product, pk=pk)
    p.is_active = not p.is_active; p.save()
    return redirect('dashboard:products')

# ── Orders ────────────────────────────────────────────────────────────────────
@staff_member_required
def order_list(request):
    status_filter = request.GET.get('status','')
    orders = Order.objects.select_related('user').all()
    if status_filter: orders = orders.filter(status=status_filter)
    return render(request, 'dashboard/orders/list.html', {
        'orders': orders, 'status_filter': status_filter,
        'statuses': Order.STATUS_CHOICES,
    })

@staff_member_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('note','')
        location = request.POST.get('location','')
        if new_status:
            order.status = new_status
            if new_status == 'shipped' and not order.tracking_number:
                order.tracking_number = request.POST.get('tracking_number','')
                order.courier_name = request.POST.get('courier_name','')
            if new_status == 'out_for_delivery' and order.user:
                send_order_email(order.user, order, 'out_for_delivery')
                notify(order.user, f'Your order #{order.order_number} is out for delivery! 🛵',
                       f'OTP for delivery confirmation: {order.delivery_otp}', 'delivery', f'/orders/{order.order_number}/')
            order.save()
            OrderStatusLog.objects.create(order=order, status=new_status, note=note, location=location)
            messages.success(request, f'Order status updated to {new_status}.')
    logs = order.logs.all()
    return render(request, 'dashboard/orders/detail.html', {
        'order': order, 'logs': logs, 'statuses': Order.STATUS_CHOICES,
    })

# ── Customers ─────────────────────────────────────────────────────────────────
@staff_member_required
def customer_list(request):
    q = request.GET.get('q','')
    customers = User.objects.filter(is_staff=False).annotate(order_count=Count('orders'))
    if q: customers = customers.filter(email__icontains=q)
    return render(request, 'dashboard/customers/list.html', {'customers': customers, 'q': q})

@staff_member_required
def customer_detail(request, pk):
    customer = get_object_or_404(User, pk=pk)
    orders = customer.orders.all()
    total_spent = orders.aggregate(s=Sum('total'))['s'] or 0
    return render(request, 'dashboard/customers/detail.html', {
        'customer': customer, 'orders': orders, 'total_spent': total_spent,
    })

# ── Categories ────────────────────────────────────────────────────────────────
@staff_member_required
def category_list(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    return render(request, 'dashboard/categories/list.html', {'categories': categories})

@staff_member_required
def category_form(request, pk=None):
    from .forms import CategoryForm
    cat = get_object_or_404(Category, pk=pk) if pk else None
    form = CategoryForm(request.POST or None, request.FILES or None, instance=cat)
    if form.is_valid():
        form.save(); messages.success(request, 'Category saved!')
        return redirect('dashboard:categories')
    return render(request, 'dashboard/categories/form.html', {'form': form, 'cat': cat})

@staff_member_required
def category_delete(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat.delete(); messages.success(request, 'Category deleted.')
        return redirect('dashboard:categories')
    return render(request, 'dashboard/categories/form.html', {'cat': cat, 'confirm_delete': True})

# ── Coupons ───────────────────────────────────────────────────────────────────
@staff_member_required
def coupon_list(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    return render(request, 'dashboard/coupons/list.html', {'coupons': coupons})

@staff_member_required
def coupon_form(request, pk=None):
    from .forms import CouponForm
    coupon = get_object_or_404(Coupon, pk=pk) if pk else None
    form = CouponForm(request.POST or None, instance=coupon)
    if form.is_valid():
        form.save(); messages.success(request, 'Coupon saved!')
        return redirect('dashboard:coupons')
    return render(request, 'dashboard/coupons/form.html', {'form': form, 'coupon': coupon})

@staff_member_required
def coupon_delete(request, pk):
    c = get_object_or_404(Coupon, pk=pk)
    c.delete(); messages.success(request, 'Coupon deleted.')
    return redirect('dashboard:coupons')

# ── Special Offers ────────────────────────────────────────────────────────────
@staff_member_required
def offer_list(request):
    offers = SpecialOffer.objects.all().order_by('-created_at')
    return render(request, 'dashboard/offers/list.html', {'offers': offers})

@staff_member_required
def offer_form(request, pk=None):
    from .forms import SpecialOfferForm
    offer = get_object_or_404(SpecialOffer, pk=pk) if pk else None
    form = SpecialOfferForm(request.POST or None, request.FILES or None, instance=offer)
    if form.is_valid():
        form.save(); messages.success(request, 'Offer saved!')
        return redirect('dashboard:offers')
    return render(request, 'dashboard/offers/form.html', {'form': form, 'offer': offer})

@staff_member_required
def offer_delete(request, pk):
    o = get_object_or_404(SpecialOffer, pk=pk)
    o.delete(); messages.success(request, 'Offer deleted.')
    return redirect('dashboard:offers')
