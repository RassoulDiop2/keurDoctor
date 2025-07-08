from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-0_p^430zgi-da9$d-k13a7#6+m^=k6yl7nlc597kz^kpiddk79'

DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'mozilla_django_oidc',
    'comptes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'keur_Doctor_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'keur_Doctor_app.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'KeurDoctorBD',
        'USER': 'postgres',
        'PASSWORD':'Diop2222',
        'HOST':'localhost',
        'PORT': '5432',
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ==================== KEYCLOAK/OIDC CONFIGURATION ====================

# Server Configuration
KEYCLOAK_SERVER_URL = "http://localhost:8080"
OIDC_REALM = "KeurDoctorSecure"
BASE_OIDC_URL = f"{KEYCLOAK_SERVER_URL}/realms/{OIDC_REALM}"

# Client Configuration
OIDC_RP_CLIENT_ID = "django-KDclient"
OIDC_RP_CLIENT_SECRET = "68Az7iaJfiJ7Xb04hdtbiLE7vnitC9BB"

# Endpoints
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/certs"
OIDC_OP_LOGOUT_URL = f"{BASE_OIDC_URL}/protocol/openid-connect/logout"
OIDC_OP_ISSUER = BASE_OIDC_URL

# OIDC Settings
OIDC_RP_SIGN_ALGO = 'RS256'
OIDC_RP_SCOPES = 'openid email profile roles'
OIDC_STORE_ACCESS_TOKEN = True
OIDC_STORE_ID_TOKEN = True
OIDC_STORE_USERINFO = True
OIDC_VERIFY_SSL = False  # True in production

# Admin Configuration (for session invalidation)
KEYCLOAK_ADMIN_USER = "admin"
KEYCLOAK_ADMIN_PASSWORD = "admin"

# Session Configuration
SESSION_COOKIE_NAME = 'keurdoctor_session'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_SECURE = False  # True in production
SESSION_COOKIE_DOMAIN = None  # Set to '.yourdomain.com' in production
CSRF_COOKIE_SECURE = False  # True in production

# Redirect URLs
LOGIN_URL = '/oidc/authenticate/'
LOGIN_REDIRECT_URL = '/redirection/'
LOGOUT_REDIRECT_URL = '/administrateur/'
OIDC_OP_LOGOUT_REDIRECT_URL = 'http://127.0.0.1:8000/'

# Token Settings
OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = 3600
OIDC_USE_NONCE = True
OIDC_NONCE_SIZE = 32
OIDC_STATE_SIZE = 32

# ==================== LOGGING CONFIGURATION ====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'mozilla_django_oidc': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'comptes': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# ==================== AUTHENTICATION BACKENDS ====================

AUTHENTICATION_BACKENDS = (
    'comptes.auth_backends.KeycloakOIDCAuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# ==================== CUSTOM USER MODEL ====================
AUTH_USER_MODEL = 'comptes.Utilisateur'