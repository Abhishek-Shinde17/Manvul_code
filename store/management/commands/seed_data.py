from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from store.models import Category, Brand, Product, ProductVariant, Coupon, SpecialOffer

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed ManVault with sample data'

    def handle(self, *args, **kwargs):
        # Admin user
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@manvault.com', 'admin123', first_name='Admin', last_name='ManVault')
            self.stdout.write('✓ Admin created (admin / admin123)')

        # Test user
        if not User.objects.filter(username='testuser').exists():
            u = User.objects.create_user('testuser', 'test@manvault.com', 'test123', first_name='Arjun', last_name='Sharma')
            u.email_verified = True; u.loyalty_points = 250; u.save()
            self.stdout.write('✓ Test user created (testuser / test123)')

        # Brand
        brand, _ = Brand.objects.get_or_create(name='ManVault', defaults={'slug': 'manvault', 'is_active': True})

        # Categories
        cats_data = [
            ('Shirts', 'shirts', '👔'), ('Jackets', 'jackets', '🧥'),
            ('T-Shirts', 't-shirts', '👕'), ('Trousers', 'trousers', '👖'),
            ('Ethnic Wear', 'ethnic-wear', '🎽'), ('Accessories', 'accessories', '⌚'),
        ]
        cats = {}
        for name, slug, icon in cats_data:
            c, _ = Category.objects.get_or_create(slug=slug, defaults={'name': name, 'icon': icon, 'is_active': True})
            cats[slug] = c
        self.stdout.write(f'✓ {len(cats)} categories')

        # Products
        products_data = [
            ('Premium Oxford Shirt', 'shirts', 1999, 2999, 'new', True, 50),
            ('Slim Fit Linen Shirt', 'shirts', 1499, 1999, 'hot', True, 30),
            ('Biker Leather Jacket', 'jackets', 5999, 8999, 'trending', True, 15),
            ('Denim Jacket Classic', 'jackets', 3499, 4999, 'sale', False, 20),
            ('Graphic Print Tee', 't-shirts', 799, 1199, 'new', True, 80),
            ('Essential White Tee', 't-shirts', 599, 999, '', False, 100),
            ('Slim Fit Chinos', 'trousers', 1999, 2999, 'hot', True, 40),
            ('Formal Trousers', 'trousers', 2499, 3499, '', False, 25),
            ('Nehru Jacket', 'ethnic-wear', 3999, 5999, 'new', True, 10),
            ('Kurta Set', 'ethnic-wear', 2999, 4999, 'trending', True, 20),
            ('Leather Wallet', 'accessories', 999, 1499, 'hot', True, 60),
            ('Classic Wristwatch', 'accessories', 4999, 7999, 'sale', True, 8),
        ]
        for name, cat_slug, price, orig, badge, featured, stock in products_data:
            import re
            slug = re.sub(r'[^a-z0-9-]', '-', name.lower()).strip('-')
            slug = re.sub(r'-+', '-', slug)
            p, created = Product.objects.get_or_create(slug=slug, defaults={
                'name': name, 'category': cats[cat_slug], 'brand': brand,
                'price': price, 'original_price': orig, 'badge': badge,
                'is_featured': featured, 'stock': stock, 'is_active': True,
                'rating': 4.2, 'review_count': 18, 'sales_count': stock//3,
                'description': f'Premium quality {name.lower()} crafted for the modern gentleman.',
                'material': 'Premium Cotton Blend',
            })
            if created:
                sizes = ['XS','S','M','L','XL','XXL'] if cat_slug != 'accessories' else ['One Size']
                for size in sizes:
                    ProductVariant.objects.get_or_create(product=p, size=size, defaults={'stock': stock//len(sizes)})
        self.stdout.write(f'✓ {len(products_data)} products')

        # Coupons
        now = timezone.now()
        coupons_data = [
            ('WELCOME10', 'percent', 10, 499, 200, 1000, 1, True),
            ('FLAT200', 'flat', 200, 999, None, 500, 2, True),
            ('SAVE50', 'percent', 50, 1999, 500, 200, 1, True),
            ('NEWUSER', 'flat', 500, 2999, None, 100, 1, True),
            ('MV15', 'percent', 15, 1499, 300, 300, 3, True),
        ]
        for code, dtype, val, minord, maxdisc, maxuses, maxperuser, active in coupons_data:
            Coupon.objects.get_or_create(code=code, defaults={
                'discount_type': dtype, 'value': val, 'min_order': minord,
                'max_discount': maxdisc, 'max_uses': maxuses,
                'max_uses_per_user': maxperuser, 'is_active': active,
                'valid_from': now, 'valid_to': now + timedelta(days=90),
                'description': f'{"Flat ₹"+str(val) if dtype=="flat" else str(val)+"%" } off on orders above ₹{minord}',
            })
        self.stdout.write('✓ 5 coupons')

        # Special Offers
        SpecialOffer.objects.get_or_create(name='Flash Friday Sale', defaults={
            'offer_type': 'flash', 'description': 'Mega flash sale on all jackets and shirts!',
            'discount_percent': 30, 'is_active': True,
            'valid_from': now, 'valid_to': now + timedelta(days=3),
        })
        SpecialOffer.objects.get_or_create(name='Buy 2 Get 1 Free', defaults={
            'offer_type': 'bxgy', 'description': 'Buy any 2 T-Shirts, get 1 free!',
            'buy_quantity': 2, 'get_quantity': 1, 'is_active': True,
            'valid_from': now, 'valid_to': now + timedelta(days=30),
        })
        SpecialOffer.objects.get_or_create(name='Loyalty Bonus Weekend', defaults={
            'offer_type': 'loyalty', 'description': 'Earn 2x loyalty points this weekend!',
            'loyalty_points_multiplier': 2.0, 'is_active': True,
            'valid_from': now, 'valid_to': now + timedelta(days=7),
        })
        self.stdout.write('✓ Special offers created')
        self.stdout.write(self.style.SUCCESS('\n🎉 ManVault seeded! Run: python manage.py runserver'))
