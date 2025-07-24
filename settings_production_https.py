# Configuration HTTPS pour Production - KeurDoctor
# Ce fichier contient les paramètres pour un déploiement HTTPS sécurisé

# À ajouter à settings.py pour la production:

# ==================== CONFIGURATION HTTPS PRODUCTION ====================

# Forcer HTTPS pour toutes les connexions
SECURE_SSL_REDIRECT = True  # Redirection automatique HTTP → HTTPS
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Cookies sécurisés (HTTPS uniquement)
SESSION_COOKIE_SECURE = True  # Cookies de session uniquement via HTTPS
CSRF_COOKIE_SECURE = True     # Cookies CSRF uniquement via HTTPS
SESSION_COOKIE_SAMESITE = 'Strict'  # Protection CSRF stricte
CSRF_COOKIE_SAMESITE = 'Strict'     # Protection CSRF stricte

# HSTS (HTTP Strict Transport Security) - Production
SECURE_HSTS_SECONDS = 31536000  # 1 an
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# En-têtes de sécurité renforcés
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
X_FRAME_OPTIONS = 'DENY'

# Configuration SSL stricte pour Keycloak/OIDC
OIDC_VERIFY_SSL = True  # Validation SSL stricte en production

# URLs HTTPS pour la production
# Remplacer les URLs de développement par les URLs de production
KEYCLOAK_SERVER_URL = "https://keycloak.yourdomain.com"
OIDC_OP_LOGOUT_REDIRECT_URL = 'https://yourdomain.com/'

# Domaines autorisés en production
ALLOWED_HOSTS = [
    'yourdomain.com',
    'www.yourdomain.com',
    'keurdoctor.yourdomain.com',
]

# Désactiver le mode DEBUG en production
DEBUG = False

# Clé secrète de production (générer une nouvelle clé)
# SECRET_KEY = 'your-production-secret-key-here'

# Base de données de production avec SSL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'keurdoctor_prod',
        'USER': 'keurdoctor_user',
        'PASSWORD': 'secure_password_here',
        'HOST': 'db.yourdomain.com',
        'PORT': '5432',
        'OPTIONS': {
            'sslmode': 'require',  # SSL obligatoire
        },
    }
}

# Configuration de logging pour production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/keurdoctor/django.log',
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': '/var/log/keurdoctor/security.log',
            'formatter': 'verbose',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'comptes.security': {
            'handlers': ['security_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}

# Configuration des fichiers statiques pour production
STATIC_ROOT = '/var/www/keurdoctor/static/'
MEDIA_ROOT = '/var/www/keurdoctor/media/'

# Configuration email pour production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yourdomain.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'noreply@yourdomain.com'
EMAIL_HOST_PASSWORD = 'email_password_here'
DEFAULT_FROM_EMAIL = 'KeurDoctor <noreply@yourdomain.com>'

# ==================== INSTRUCTIONS DE DÉPLOIEMENT ====================

"""
Pour déployer en production avec HTTPS complet:

1. Certificats SSL:
   - Utilisez Let's Encrypt: certbot --nginx -d yourdomain.com
   - Ou un certificat commercial

2. Serveur Web (Nginx):
   server {
       listen 443 ssl http2;
       server_name yourdomain.com;
       
       ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
       ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Forwarded-Proto https;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
       }
   }

3. Variables d'environnement:
   export DJANGO_SETTINGS_MODULE=keur_Doctor_app.settings_production
   export SECRET_KEY=your-production-secret-key
   export DATABASE_PASSWORD=your-db-password

4. Commandes de déploiement:
   python manage.py collectstatic --noinput
   python manage.py migrate
   python manage.py check --deploy

5. Serveur d'application:
   gunicorn keur_Doctor_app.wsgi:application --bind 127.0.0.1:8000
"""
