from django.urls import path
from . import views
from comptes.views import user_management

urlpatterns = [
    # Page d'accueil
    path('', views.HomeView.as_view(), name='home'),
    
    # Inscription
    path('inscription/', views.inscription_view, name='inscription'),
    
    # Redirection après connexion
    path('redirection/', views.redirection_role, name='redirection_role'),
    
    # Dashboards par rôle
    path('administration/', views.admin_dashboard, name='admin_dashboard'),
    path('administration/users/', user_management, name='user_management'),
    path('administration/users/create/', views.create_user_view, name='create_user'),
    path('administration/securite/', views.gestion_securite, name='gestion_securite'),
    path('medecin/', views.medecin_dashboard, name='medecin_dashboard'),
    path('patient/', views.patient_dashboard, name='patient_dashboard'),
    path('compte/', views.default_dashboard, name='default_dashboard'),

    # Actions rapides admin métier
    path('administration/debloquer/<int:user_id>/', views.debloquer_utilisateur, name='debloquer_utilisateur'),
    path('administration/alerte-lue/<int:alerte_id>/', views.marquer_alerte_lue, name='marquer_alerte_lue'),
    path('administration/definir-role/<int:user_id>/', views.definir_role_utilisateur, name='definir_role_utilisateur'),
    path('administration/sync-keycloak/<int:user_id>/', views.synchroniser_utilisateur_keycloak, name='synchroniser_utilisateur_keycloak'),

    # Profil utilisateur
    path('profil/', views.profile_view, name='profile'),
    
    # API
    path('api/user-info/', views.user_info, name='user_info'),
    path('api/set-role/', views.set_role_session, name='set_role_session'),
    
    # Déconnexion personnalisée
    path('logout/', views.custom_logout, name='custom_logout'),
]