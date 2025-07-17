from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from comptes.views_rfid import scan_rfid_uid

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('comptes.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('administration/scan-rfid/', scan_rfid_uid, name='scan_rfid_admin_metier'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)