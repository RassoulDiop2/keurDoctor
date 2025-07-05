from django.urls import path
from . import views
from comptes.views import user_management

urlpatterns = [
    # Page d'accueil
    path('', views.HomeView.as_view(), name='home'),
    
    # Inscription
    path('inscription/', views.inscription_view, name='inscription'),
    path('inscription/success/', views.inscription_success_view, name='inscription_success'),
    
    # Redirection après connexion
    path('redirection/', views.redirection_role, name='redirection_role'),
    
    # Dashboards par rôle
    path('admin/', views.admin_dashboard, name='admin_dashboard'),
    path('administrateur/', views.admin_dashboard, name='admin_dashboard'),
    path('medecin/', views.medecin_dashboard, name='medecin_dashboard'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('compte/', views.default_dashboard, name='default_dashboard'),

    # La gestion des utilisateurs
    path('admin/users/', user_management, name='user_management'),

    # Profil utilisateur
    path('profil/', views.profile_view, name='profile'),
    
    # API utilisateur
    path('api/user-info/', views.user_info, name='user_info'),
    
    # Déconnexion personnalisée
    path('logout/', views.custom_logout, name='custom_logout'),
]