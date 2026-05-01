from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import User, Address

def style(f): f.widget.attrs.update({'class':'form-control mv-input'}); return f

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    phone = forms.CharField(max_length=15, required=False)
    class Meta:
        model = User
        fields = ['first_name','last_name','email','username','phone','password1','password2']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs.update({'class':'form-control mv-input'})

class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs.update({'class':'form-control mv-input'})

class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','email','phone','date_of_birth','gender','avatar']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs.update({'class':'form-control mv-input'})

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['label','full_name','phone','line1','line2','city','state','pincode','country','is_default']
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values(): f.widget.attrs.update({'class':'form-control mv-input'})
