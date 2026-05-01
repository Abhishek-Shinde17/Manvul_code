from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Address, OTPVerification
from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm
from notifications.utils import notify, send_otp_email


def register_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        otp  = OTPVerification.objects.create(user=user, otp_type='email_verify')
        try:
            send_otp_email(user, otp.code, 'email verification')
            messages.success(request, f'Account created! OTP sent to {user.email}. Check your inbox (and spam folder).')
        except Exception as e:
            messages.warning(request,
                f'Account created but OTP email failed to send ({e}). '
                f'Your OTP is <strong>{otp.code}</strong> — use it below.')
        request.session['verify_user_id'] = user.id
        return redirect('accounts:verify_email')
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('store:home')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Welcome back, {user.first_name or user.username}!')
        return redirect(request.GET.get('next', 'store:home'))
    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'You have been signed out.')
    return redirect('store:home')


def verify_email(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        return redirect('accounts:login')
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        code = request.POST.get('otp', '').strip()
        otp  = OTPVerification.objects.filter(
            user=user, otp_type='email_verify', is_used=False).last()
        if otp and otp.is_valid and otp.code == code:
            otp.is_used = True; otp.save()
            user.email_verified = True; user.save()
            login(request, user)
            del request.session['verify_user_id']
            notify(user, 'Welcome to ManVault! 🎉', 'Your email is verified. Happy shopping!', 'system')
            messages.success(request, 'Email verified! Welcome to ManVault 🎉')
            return redirect('store:home')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again or request a new one.')
    return render(request, 'accounts/verify_email.html', {'user': user})


def resend_otp(request):
    user_id = request.session.get('verify_user_id')
    if not user_id:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('accounts:register')
    user = get_object_or_404(User, id=user_id)
    # Invalidate all previous OTPs
    OTPVerification.objects.filter(user=user, otp_type='email_verify', is_used=False).update(is_used=True)
    otp = OTPVerification.objects.create(user=user, otp_type='email_verify')
    try:
        send_otp_email(user, otp.code, 'email verification')
        messages.success(request, f'New OTP sent to {user.email}! Check your inbox and spam folder.')
    except Exception as e:
        messages.warning(request,
            f'Email failed to send ({e}). '
            f'Your OTP is <strong>{otp.code}</strong>.')
    return redirect('accounts:verify_email')


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        try:
            user = User.objects.get(email=email)
            OTPVerification.objects.filter(user=user, otp_type='password_reset', is_used=False).update(is_used=True)
            otp  = OTPVerification.objects.create(user=user, otp_type='password_reset')
            try:
                send_otp_email(user, otp.code, 'password reset')
                messages.success(request, f'OTP sent to {user.email}! Check your inbox and spam folder.')
            except Exception as e:
                messages.warning(request,
                    f'Email failed to send. Your OTP is <strong>{otp.code}</strong>.')
            request.session['reset_user_id'] = user.id
            return redirect('accounts:reset_password')
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    return render(request, 'accounts/forgot_password.html')


def reset_password(request):
    user_id = request.session.get('reset_user_id')
    if not user_id:
        return redirect('accounts:forgot_password')
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        code     = request.POST.get('otp', '').strip()
        new_pass = request.POST.get('new_password', '')
        if len(new_pass) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
            return render(request, 'accounts/reset_password.html')
        otp = OTPVerification.objects.filter(
            user=user, otp_type='password_reset', is_used=False).last()
        if otp and otp.is_valid and otp.code == code:
            otp.is_used = True; otp.save()
            user.set_password(new_pass); user.save()
            del request.session['reset_user_id']
            messages.success(request, 'Password reset successfully! Please log in.')
            return redirect('accounts:login')
        else:
            messages.error(request, 'Invalid or expired OTP. Please try again.')
    return render(request, 'accounts/reset_password.html')


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    addresses = request.user.addresses.all()
    from orders.models import Order
    orders = request.user.orders.all()[:5]
    try:    wishlist_count = request.user.wishlist.products.count()
    except: wishlist_count = 0
    return render(request, 'accounts/profile.html', {
        'form': form, 'addresses': addresses,
        'orders': orders, 'wishlist_count': wishlist_count,
    })


@login_required
def add_address(request):
    form = AddressForm(request.POST or None)
    if form.is_valid():
        addr = form.save(commit=False); addr.user = request.user; addr.save()
        messages.success(request, 'Address added!')
        return redirect(request.POST.get('next', 'accounts:profile'))
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Add Address'})


@login_required
def edit_address(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    form = AddressForm(request.POST or None, instance=addr)
    if form.is_valid():
        form.save(); messages.success(request, 'Address updated!')
        return redirect('accounts:profile')
    return render(request, 'accounts/address_form.html', {'form': form, 'title': 'Edit Address'})


@login_required
def delete_address(request, pk):
    addr = get_object_or_404(Address, pk=pk, user=request.user)
    addr.delete(); messages.success(request, 'Address removed.')
    return redirect('accounts:profile')