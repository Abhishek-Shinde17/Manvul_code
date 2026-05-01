from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class AccountAdapter(DefaultAccountAdapter):
    """
    Overrides allauth's built-in login/signup URLs so they always
    point to our custom ManVault pages, not allauth's default pages.
    """
    def is_open_for_signup(self, request):
        return True

    def get_login_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL

    def get_signup_redirect_url(self, request):
        return settings.LOGIN_REDIRECT_URL


class SocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Called after Google returns user data.
    - Marks the user's email as verified (no OTP needed for Google users)
    - Sets is_google_account = True
    - Copies first/last name from Google profile
    """
    def is_open_for_signup(self, request, sociallogin):
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        # Mark email as verified — Google already verified it
        user.email_verified    = True
        user.is_google_account = True

        # Copy name from Google profile if not already set
        extra = sociallogin.account.extra_data
        if not user.first_name and extra.get('given_name'):
            user.first_name = extra['given_name']
        if not user.last_name and extra.get('family_name'):
            user.last_name = extra['family_name']

        # Give welcome loyalty points on first signup via Google
        if not user.loyalty_points:
            user.loyalty_points = 50   # welcome bonus

        user.save()
        return user

    def get_connect_redirect_url(self, request, socialaccount):
        return '/'
