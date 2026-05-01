from django import forms
from store.models import Product, Category, Coupon, SpecialOffer

STYLE = {'class': 'form-control mv-input'}

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
class ProductForm(forms.ModelForm):
    images = forms.FileField(
        # widget=MultipleFileInput(attrs={
        #     'multiple': True,
        #     'class': 'form-control mv-input',
        #     'accept': 'image/*'
        # }),
        required=False,
    )
    class Meta:
        model = Product
        fields = ['name','slug','category','brand','description','material','price','original_price','stock','badge','is_active','is_featured']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if not hasattr(f.widget, 'attrs'): continue
            f.widget.attrs.update(STYLE)

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name','slug','description','icon','image','is_active']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            if hasattr(f.widget, 'attrs'): f.widget.attrs.update(STYLE)

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = ['code','description','discount_type','value','min_order','max_discount','max_uses','max_uses_per_user','is_active','valid_from','valid_to','first_order_only']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', **STYLE}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', **STYLE}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if hasattr(f.widget, 'attrs') and name not in ['valid_from','valid_to']:
                f.widget.attrs.update(STYLE)

class SpecialOfferForm(forms.ModelForm):
    class Meta:
        model = SpecialOffer
        fields = ['name','offer_type','description','discount_percent','discount_flat','buy_quantity','get_quantity','valid_from','valid_to','is_active','banner_image']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local', **STYLE}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local', **STYLE}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, f in self.fields.items():
            if hasattr(f.widget, 'attrs') and name not in ['valid_from','valid_to']:
                f.widget.attrs.update(STYLE)
