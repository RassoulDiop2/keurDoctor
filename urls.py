from django.urls import path
from comptes.views_rfid import scan_rfid_uid
from comptes import views

urlpatterns = [
    # URLs principales
    path('', views.HomeView.as_view(), name='home'),
    path('redirection/', views.redirection_role, name='redirection_role'),
    path('profil/', views.profile_view, name='profile'),
    path('logout/', views.custom_logout, name='logout'),
    
    # URLs d'authentification
    path('licence/', views.licence_view, name='licence'),
    path('inscription/', views.inscription_view, name='inscription'),
    path('set-role/', views.set_role_session, name='set_role_session'),
    
    # URLs d'administration
    path('administration/', views.admin_dashboard, name='admin_dashboard'),
    path('administration/users/', views.user_management, name='user_management'),
    path('administration/users/create/', views.create_user_view, name='create_user'),
    path('administration/securite/', views.gestion_securite, name='gestion_securite'),
    path('administration/debloquer/<int:user_id>/', views.debloquer_utilisateur, name='debloquer_utilisateur'),
    path('administration/role/<int:user_id>/', views.definir_role_utilisateur, name='definir_role_utilisateur'),
    path('administration/alerte/<int:alerte_id>/lue/', views.marquer_alerte_lue, name='marquer_alerte_lue'),
    path('administration/sync/<int:user_id>/', views.synchroniser_utilisateur_keycloak, name='synchroniser_utilisateur_keycloak'),
    
    # URLs RFID
    path('admin/scan-rfid-uid/', scan_rfid_uid, name='scan_rfid_uid'),
    path('administration/scan-rfid/', scan_rfid_uid, name='scan_rfid_admin_metier'),
    
    # URLs des dashboards
    path('dashboard/medecin/', views.medecin_dashboard, name='medecin_dashboard'),
    path('dashboard/patient/', views.patient_dashboard, name='patient_dashboard'),
    path('dashboard/default/', views.default_dashboard, name='default_dashboard'),
    
    # URLs de test
    path('test/auth/', views.TestAuthView.as_view(), name='test_auth'),
    path('test/medecin/', views.test_acces_medecin, name='test_acces_medecin'),
    path('test/admin/', views.test_acces_admin, name='test_acces_admin'),
    path('test/patient/', views.test_acces_patient, name='test_acces_patient'),
    path('test/securite/', views.test_securite_page, name='test_securite'),
    
    # URLs RFID
    path('rfid/login/', views.patient_rfid_login, name='patient_rfid_login'),
    path('rfid/otp/', views.patient_rfid_otp, name='patient_rfid_otp'),
    path('rfid/wait/', views.rfid_wait_view, name='rfid_wait'),
    path('rfid/register/', views.enregistrer_rfid_view, name='enregistrer_rfid'),
    path('rfid/register/<int:user_id>/', views.enregistrer_rfid_admin_view, name='enregistrer_rfid_admin'),
    path('rfid/methodes/', views.methodes_authentification, name='methodes_authentification'),
    
    # APIs RFID
    path('api/rfid/auth/', views.api_rfid_auth, name='api_rfid_auth'),
    path('api/rfid/patient-auth/', views.api_rfid_patient_auth, name='api_rfid_patient_auth'),
    
    # URLs d'information utilisateur
    path('user/info/', views.user_info, name='user_info'),
] 