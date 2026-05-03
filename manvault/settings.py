import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-manvault-secret-key-change-in-production-2024'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'crispy_forms',
    'crispy_bootstrap5',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'accounts',
    'store',
    'orders',
    'dashboard',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'manvault.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.cart_processor',
                'store.context_processors.wishlist_processor',
                'store.context_processors.common_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'manvault.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.User'

# ── Authentication backends ───────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    #'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1

# ── URL redirects ─────────────────────────────────────────────────────────────
LOGIN_URL           = '/accounts/login/'   # Our custom login, NOT /social/login/
LOGIN_REDIRECT_URL  = '/'
LOGOUT_REDIRECT_URL = '/'


CSRF_TRUSTED_ORIGINS = [
    "https://*.cloudshell.dev",
    "https://*.ngrok-free.app",
    "https://*.ngrok-free.dev",
    "https://manvulcode-production.up.railway.app"
]
# ── django-allauth core ───────────────────────────────────────────────────────
ACCOUNT_LOGIN_METHODS         = {'username', 'email'}
ACCOUNT_SIGNUP_FIELDS         = ['email*', 'username*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION    = 'none'
ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'    # change to 'https' in production

# Force allauth's own pages to redirect to OUR custom pages
ACCOUNT_LOGIN_URL  = '/accounts/login/'
ACCOUNT_SIGNUP_URL = '/accounts/register/'

# Social account behaviour
SOCIALACCOUNT_AUTO_SIGNUP    = True   # auto-create account on first Google login
SOCIALACCOUNT_LOGIN_ON_GET   = True   # skip the extra "confirm?" screen
SOCIALACCOUNT_EMAIL_REQUIRED = True

# ── Custom adapters (set email_verified=True for Google users) ────────────────
ACCOUNT_ADAPTER       = 'accounts.adapter.AccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.SocialAccountAdapter'

# ── Google OAuth provider ─────────────────────────────────────────────────────
# Credentials are stored in the Django admin under Social Applications.
# Do NOT hardcode them here.
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'OAUTH_PKCE_ENABLED': True,
    }
}

# ── Crispy Forms ──────────────────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK          = 'bootstrap5'

# ── Logging — see email errors in the terminal ────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {'class': 'logging.StreamHandler'},
    },
    'loggers': {
        'notifications': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
        'django.core.mail': {'handlers': ['console'], 'level': 'DEBUG', 'propagate': True},
    },
}
# ── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL')

OTP_EXPIRY_MINUTES = 10
STRIPE_PUBLIC_KEY  = 'pk_test_your_stripe_public_key'
STRIPE_SECRET_KEY  = 'sk_test_your_stripe_secret_key'
SESSION_COOKIE_AGE = 86400 * 30
