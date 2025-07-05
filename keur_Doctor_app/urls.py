from django.contrib import admin
from django.urls import path, include
from mozilla_django_oidc.views import OIDCLogoutView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('comptes.urls')),
    path('oidc/', include('mozilla_django_oidc.urls')),
    path('oidc/logout/', OIDCLogoutView.as_view(), name='oidc_logout'),
]