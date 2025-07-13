from django.urls import path
from . import views
from comptes.views import user_management
from .views import api_rfid_auth, enregistrer_rfid_view, enregistrer_rfid_admin_view, rfid_wait_view

urlpatterns = [
    # Page d'accueil
    path('', views.HomeView.as_view(), name='home'),
    
    # Licence et politique de confidentialité
    path('licence/', views.licence_view, name='licence'),
    
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
    path('api/rfid-auth/', api_rfid_auth, name='api_rfid_auth'),
    
    # Déconnexion personnalisée
    path('logout/', views.custom_logout, name='custom_logout'),
    
    # URLs de test pour la sécurité
    path('test/securite/', views.test_securite_page, name='test_securite_page'),
    path('test/acces/medecin/', views.test_acces_medecin, name='test_acces_medecin'),
    path('test/acces/admin/', views.test_acces_admin, name='test_acces_admin'),
    path('test/acces/patient/', views.test_acces_patient, name='test_acces_patient'),
    
    # URLs pour simuler les tentatives d'usurpation
    path('test/usurpation/<str:role_cible>/', views.simuler_usurpation_role, name='simuler_usurpation_role'),
    path('test/elevation/', views.simuler_elevation_privileges, name='simuler_elevation_privileges'),
    path('test/acces-direct/<str:url_cible>/', views.simuler_acces_direct_url, name='simuler_acces_direct_url'),

    # RFID
    path('rfid/enregistrer/', enregistrer_rfid_view, name='enregistrer_rfid'),
    path('rfid/enregistrer/<int:user_id>/', enregistrer_rfid_admin_view, name='enregistrer_rfid_admin'),
    path('rfid/attente/', rfid_wait_view, name='rfid_wait'),


]