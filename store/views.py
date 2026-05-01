from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from .models import (Product, Category, Brand, Cart, CartItem, Wishlist,
                     Review, ProductVariant, Coupon, CouponUsage, SpecialOffer)
from .forms import ReviewForm

BADGE_CHOICES = [('new','New Arrivals'),('hot','Hot Deals'),('sale','On Sale'),('trending','Trending')]

def get_or_create_cart(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
        return cart
    if not request.session.session_key:
        request.session.create()
    cart, _ = Cart.objects.get_or_create(session_key=request.session.session_key, user=None)
    return cart

def home(request):
    featured = Product.objects.filter(is_active=True, is_featured=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True, badge='new')[:8]
    categories = Category.objects.filter(is_active=True)[:6]
    now = timezone.now()
    flash_offers = SpecialOffer.objects.filter(is_active=True, offer_type='flash', valid_from__lte=now, valid_to__gte=now)[:3]
    special_offers = SpecialOffer.objects.filter(is_active=True, valid_from__lte=now, valid_to__gte=now)[:4]
    return render(request, 'store/home.html', {
        'featured': featured, 'new_arrivals': new_arrivals,
        'categories': categories, 'flash_offers': flash_offers,
        'special_offers': special_offers,
    })

def shop(request):
    products = Product.objects.filter(is_active=True)
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    q = request.GET.get('q',''); cat = request.GET.get('category','')
    brand = request.GET.get('brand',''); min_p = request.GET.get('min_price','')
    max_p = request.GET.get('max_price',''); sort = request.GET.get('sort','-created_at')
    badge = request.GET.get('badge','')
    if q: products = products.filter(Q(name__icontains=q)|Q(description__icontains=q)|Q(category__name__icontains=q))
    if cat: products = products.filter(category__slug=cat)
    if brand: products = products.filter(brand__slug=brand)
    if min_p: products = products.filter(price__gte=min_p)
    if max_p: products = products.filter(price__lte=max_p)
    if badge: products = products.filter(badge=badge)
    sort_map = {'price_asc':'price','price_desc':'-price','rating':'-rating','newest':'-created_at','popular':'-sales_count'}
    products = products.order_by(sort_map.get(sort, '-created_at'))
    paginator = Paginator(products, 16)
    page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'store/shop.html', {
        'products': page, 'categories': categories, 'brands': brands,
        'q': q, 'selected_cat': cat, 'selected_brand': brand,
        'min_price': min_p, 'max_price': max_p, 'sort': sort, 'badge': badge,
        'total_products': paginator.count, 'badges': BADGE_CHOICES,
    })

def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.all()
    related = Product.objects.filter(category=product.category, is_active=True).exclude(id=product.id)[:4]
    review_form = ReviewForm()
    if request.method == 'POST' and request.user.is_authenticated:
        review_form = ReviewForm(request.POST, request.FILES)
        if review_form.is_valid():
            r, created = Review.objects.get_or_create(product=product, user=request.user,
                defaults={'rating':review_form.cleaned_data['rating'], 'title':review_form.cleaned_data.get('title',''), 'body':review_form.cleaned_data['body']})
            if not created:
                r.rating=review_form.cleaned_data['rating']; r.body=review_form.cleaned_data['body']; r.save()
            avg = product.reviews.aggregate(Avg('rating'))['rating__avg']
            product.rating = avg or 0; product.review_count = product.reviews.count(); product.save()
            messages.success(request, 'Review submitted! ⭐')
            return redirect('store:product_detail', slug=slug)
    cart = get_or_create_cart(request)
    in_cart = cart.items.filter(product=product).exists()
    in_wishlist = False
    if request.user.is_authenticated:
        try: in_wishlist = request.user.wishlist.products.filter(id=product.id).exists()
        except: pass
    active_offers = SpecialOffer.objects.filter(is_active=True, applicable_products=product, valid_from__lte=timezone.now(), valid_to__gte=timezone.now())
    return render(request, 'store/product_detail.html', {
        'product': product, 'reviews': reviews, 'related': related,
        'review_form': review_form, 'in_cart': in_cart, 'in_wishlist': in_wishlist,
        'active_offers': active_offers,
    })

def category_view(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    products = Product.objects.filter(category=category, is_active=True)
    return render(request, 'store/shop.html', {
        'products': products, 'categories': Category.objects.filter(is_active=True),
        'brands': Brand.objects.filter(is_active=True), 'selected_cat': slug,
        'total_products': products.count(), 'badges': BADGE_CHOICES,
        'q':'','min_price':'','max_price':'','sort':'-created_at','badge':'','selected_brand':''
    })

def cart_view(request):
    cart = get_or_create_cart(request)
    coupon_id = request.session.get('coupon_id')
    coupon = None; coupon_discount = 0
    if coupon_id:
        try:
            coupon = Coupon.objects.get(id=coupon_id)
            coupon_discount = coupon.calculate_discount(cart.total)
        except: pass
    shipping = 0 if cart.total >= 999 else 99
    total = max(0, cart.total + shipping - coupon_discount)
    return render(request, 'store/cart.html', {
        'cart': cart, 'coupon': coupon, 'coupon_discount': coupon_discount,
        'shipping': shipping, 'total': total
    })

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_or_create_cart(request)
    variant_id = request.POST.get('variant_id')
    variant = ProductVariant.objects.filter(id=variant_id).first() if variant_id else None
    item, created = CartItem.objects.get_or_create(cart=cart, product=product, variant=variant)
    if not created: item.quantity += 1; item.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True, 'count': cart.item_count, 'message': f'{product.name} added!'})
    messages.success(request, f'"{product.name}" added to bag! 🛒')
    return redirect(request.META.get('HTTP_REFERER', 'store:cart'))

def remove_from_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    item.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({'success': True, 'count': cart.item_count, 'total': str(cart.total)})
    return redirect('store:cart')

def update_cart(request, item_id):
    item = get_object_or_404(CartItem, id=item_id)
    qty = int(request.POST.get('quantity', 1))
    if qty <= 0: item.delete()
    else: item.quantity = qty; item.save()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_or_create_cart(request)
        return JsonResponse({'success': True, 'total': str(cart.total), 'count': cart.item_count})
    return redirect('store:cart')

def apply_coupon(request):
    if request.method == 'POST':
        code = request.POST.get('code','').upper().strip()
        try:
            coupon = Coupon.objects.get(code=code)
            cart = get_or_create_cart(request)
            valid, msg = coupon.is_valid_for_user(request.user, cart.total)
            if valid:
                request.session['coupon_id'] = coupon.id
                disc = coupon.calculate_discount(cart.total)
                messages.success(request, f'✅ Coupon applied! You save ₹{disc:.0f}')
            else:
                messages.error(request, f'❌ {msg}')
        except Coupon.DoesNotExist:
            messages.error(request, '❌ Invalid coupon code.')
    return redirect('store:cart')

def remove_coupon(request):
    if 'coupon_id' in request.session:
        del request.session['coupon_id']
    messages.info(request, 'Coupon removed.')
    return redirect('store:cart')

def offers_page(request):
    now = timezone.now()
    offers = SpecialOffer.objects.filter(is_active=True, valid_from__lte=now, valid_to__gte=now)
    coupons = Coupon.objects.filter(is_active=True, valid_from__lte=now, valid_to__gte=now)
    steps_desc = "1. Add items to your bag,Pick products you love|2. Go to checkout,Proceed to checkout from your bag|3. Enter coupon code,Type or paste the coupon code in the field|4. Apply & save!,Your discount will be applied instantly"
    steps_list = [item.split(",") for item in steps_desc.split("|")]
    return render(request, 'store/offers.html', {'offers': offers, 'coupons': coupons, 'steps_list': steps_list})

@login_required
def wishlist_view(request):
    wl, _ = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'store/wishlist.html', {'wishlist': wl})

@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wl, _ = Wishlist.objects.get_or_create(user=request.user)
    if wl.products.filter(id=product_id).exists():
        wl.products.remove(product); added = False
    else:
        wl.products.add(product); added = True
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'added': added, 'count': wl.products.count()})
    messages.success(request, 'Added to wishlist ❤️' if added else 'Removed from wishlist')
    return redirect(request.META.get('HTTP_REFERER', 'store:wishlist'))
