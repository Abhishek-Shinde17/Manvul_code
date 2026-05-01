from .models import Cart, Wishlist, Category

def cart_processor(request):
    cart_count = 0
    try:
        if request.user.is_authenticated:
            cart = Cart.objects.filter(user=request.user).first()
        else:
            sk = request.session.session_key
            cart = Cart.objects.filter(session_key=sk, user=None).first() if sk else None
        if cart: cart_count = cart.item_count
    except: pass
    return {'cart_count': cart_count}

def wishlist_processor(request):
    wishlist_count = 0
    try:
        if request.user.is_authenticated:
            wl = Wishlist.objects.filter(user=request.user).first()
            if wl: wishlist_count = wl.products.count()
    except: pass
    return {'wishlist_count': wishlist_count}

def common_processor(request):
    cats_for_nav = []
    notif_count = 0
    try:
        cats_for_nav = Category.objects.filter(is_active=True)[:8]
        if request.user.is_authenticated:
            notif_count = request.user.notifications.filter(is_read=False).count()
    except: pass
    return {'cats_for_nav': cats_for_nav, 'notif_count': notif_count}
