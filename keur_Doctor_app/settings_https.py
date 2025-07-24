"""
Configuration de production HTTPS pour KeurDoctor
Ce fichier hérite de settings.py et ajoute les configurations spécifiques à HTTPS
"""

from .settings import *
import os

# ==================== CONFIGURATION HTTPS PRODUCTION ====================

# Mode production
DEBUG = False

# Domaines autorisés pour HTTPS
ALLOWED_HOSTS = [
    'keurdoctor.com',
    'www.keurdoctor.com',
    'secure.keurdoctor.com',
    '*.keurdoctor.com',
    'localhost',
    '127.0.0.1',
]

# ==================== SÉCURITÉ HTTPS RENFORCÉE ====================

# Force HTTPS pour toutes les connexions
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies sécurisés (HTTPS uniquement)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_SAMESITE = 'Strict'

# HSTS (HTTP Strict Transport Security) - 2 ans
SECURE_HSTS_SECONDS = 63072000  # 2 ans
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Protection contre le détournement de contenu
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Protection contre le clickjacking
X_FRAME_OPTIONS = 'DENY'

# ==================== CONFIGURATION KEYCLOAK HTTPS ====================

# URLs Keycloak en HTTPS
KEYCLOAK_SERVER_URL = os.getenv('KEYCLOAK_SERVER_URL', 'https://keycloak.keurdoctor.com')
BASE_OIDC_URL = f"{KEYCLOAK_SERVER_URL}/realms/{OIDC_REALM}"

# Endpoints OIDC sécurisés
OIDC_OP_AUTHORIZATION_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/auth"
OIDC_OP_TOKEN_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/token"
OIDC_OP_USER_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/userinfo"
OIDC_OP_JWKS_ENDPOINT = f"{BASE_OIDC_URL}/protocol/openid-connect/certs"
OIDC_OP_LOGOUT_URL = f"{BASE_OIDC_URL}/protocol/openid-connect/logout"

# Validation SSL stricte
OIDC_VERIFY_SSL = True

# URLs de redirection sécurisées
OIDC_OP_LOGOUT_REDIRECT_URL = 'https://keurdoctor.com/'

# ==================== BASE DE DONNÉES PRODUCTION ====================

# Configuration PostgreSQL sécurisée
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'keurdoctor_prod'),
        'USER': os.getenv('DB_USER', 'keurdoctor_user'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',  # Force SSL pour la DB
        },
    }
}

# ==================== LOGGING PRODUCTION ====================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/keurdoctor/django.log',
            'maxBytes': 1024*1024*50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/keurdoctor/security.log',
            'maxBytes': 1024*1024*50,  # 50 MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'comptes': {
            'handlers': ['file', 'security_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'mozilla_django_oidc': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
    },
}

# ==================== CACHE ET PERFORMANCE ====================

# Cache Redis pour la production
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'ssl_cert_reqs': None,  # Configuration SSL pour Redis si nécessaire
            }
        }
    }
}

# Session stockée dans Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ==================== EMAIL SÉCURISÉ ====================

# Configuration email avec TLS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@keurdoctor.com')

# ==================== VARIABLES D'ENVIRONNEMENT REQUISES ====================

# Variables d'environnement obligatoires en production
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'DB_PASSWORD',
    'OIDC_RP_CLIENT_SECRET',
    'EMAIL_HOST_PASSWORD',
    'ENCRYPTION_KEY',
]

# Vérification des variables d'environnement
for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        raise RuntimeError(f"Variable d'environnement manquante: {var}")

# ==================== SÉCURITÉ AVANCÉE ====================

# Clé secrète depuis l'environnement
SECRET_KEY = os.getenv('SECRET_KEY')

# Clé de chiffrement depuis l'environnement
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY').encode()

# Client secret OIDC depuis l'environnement
OIDC_RP_CLIENT_SECRET = os.getenv('OIDC_RP_CLIENT_SECRET')

# ==================== MONITORING ET MÉTRIQUES ====================

# Configuration pour les métriques de performance
INSTALLED_APPS += [
    'django_prometheus',  # Métriques Prometheus
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
] + MIDDLEWARE + [
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

# ==================== BACKUP ET ARCHIVAGE ====================

# Configuration pour les backups automatiques
BACKUP_DIR = '/var/backups/keurdoctor'
BACKUP_RETENTION_DAYS = 30

# ==================== CONFORMITÉ RÉGLEMENTAIRE ====================

# Audit et conformité RGPD/HIPAA
AUDIT_LOG_RETENTION_DAYS = 2555  # 7 ans
GDPR_COMPLIANCE_MODE = True
HIPAA_COMPLIANCE_MODE = True

print("🔒 Configuration HTTPS de production chargée avec succès")
