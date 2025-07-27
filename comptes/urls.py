from django.urls import path
from . import views
from comptes.views import user_management
from .views import api_rfid_auth, enregistrer_rfid_view, enregistrer_rfid_admin_view, rfid_wait_view
from .views_rfid import api_scan_rfid, patient_rfid_login, patient_rfid_otp, api_scan_rfid_for_user_creation, api_rfid_direct_auth, universal_rfid_login, universal_rfid_otp, medecin_rfid_login, medecin_rfid_otp, api_rfid_medecin_auth

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

    # Nouvelles fonctionnalités médecin
    path('medecin/patients/', views.liste_patients_medecin, name='liste_patients_medecin'),
    path('medecin/calendrier/', views.calendrier_medecin, name='calendrier_medecin'),
    path('medecin/creer-dossier/', views.creer_dossier_medical, name='creer_dossier_medical'),
    
    # Actions sur les rendez-vous médecin
    path('medecin/rdv/<int:rdv_id>/confirmer/', views.confirmer_rdv_medecin, name='confirmer_rdv_medecin'),
    path('medecin/rdv/<int:rdv_id>/annuler/', views.annuler_rdv_medecin, name='annuler_rdv_medecin'),
    path('medecin/rdv/<int:rdv_id>/terminer/', views.terminer_rdv_medecin, name='terminer_rdv_medecin'),
    
    # Nouvelles fonctionnalités patient
    path('patient/prendre-rdv/', views.prendre_rdv, name='prendre_rdv'),
    path('patient/mon-dossier/', views.mon_dossier_medical, name='mon_dossier_medical'),
    path('patient/historique-rdv/', views.historique_rdv_patient, name='historique_rdv_patient'),
    path('patient/annuler-rdv/<int:rdv_id>/', views.annuler_rdv_patient, name='annuler_rdv_patient'),
    
    # Nouvelles fonctionnalités admin
    path('administration/statistiques-detaillees/', views.statistiques_detaillees, name='statistiques_detaillees'),

    # Actions rapides admin métier
    path('administration/debloquer/<int:user_id>/', views.debloquer_utilisateur, name='debloquer_utilisateur'),
    path('administration/alerte-lue/<int:alerte_id>/', views.marquer_alerte_lue, name='marquer_alerte_lue'),
    path('administration/definir-role/<int:user_id>/', views.definir_role_utilisateur, name='definir_role_utilisateur'),
    path('administration/sync-keycloak/<int:user_id>/', views.synchroniser_utilisateur_keycloak, name='synchroniser_utilisateur_keycloak'),
    path('administration/sync-keycloak-all/', views.synchroniser_tous_utilisateurs_keycloak, name='synchroniser_tous_utilisateurs_keycloak'),
    path('administration/sync-groupes-django/', views.synchroniser_groupes_django_tous, name='synchroniser_groupes_django_tous'),
    path('administration/verifier-groupes/', views.verifier_synchronisation_groupes, name='verifier_synchronisation_groupes'),
    path('administration/statistiques/', views.admin_stats, name='admin_stats'),

    # Profil utilisateur
    path('profil/', views.profile_view, name='profile'),
    
    # API
    path('api/user-info/', views.user_info, name='user_info'),
    path('api/set-role/', views.set_role_session, name='set_role_session'),
    path('api/rfid-auth/', api_rfid_auth, name='api_rfid_auth'),
    path('api/rfid-patient-auth/', views.api_rfid_patient_auth, name='api_rfid_patient_auth'),
    
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

    # RFID Pages
    path('rfid/login/', universal_rfid_login, name='universal_rfid_login'),
    path('rfid/otp/', universal_rfid_otp, name='universal_rfid_otp'),
    path('rfid/enregistrer/', enregistrer_rfid_view, name='enregistrer_rfid'),
    path('rfid/enregistrer/<int:user_id>/', enregistrer_rfid_admin_view, name='enregistrer_rfid_admin'),
    path('rfid/attente/', rfid_wait_view, name='rfid_wait'),
    
    # Authentification RFID pour patients
    path('patient/rfid/login/', views.patient_rfid_login, name='patient_rfid_login'),
    path('patient/rfid/otp/', views.patient_rfid_otp, name='patient_rfid_otp'),
    
    # Authentification RFID pour médecins  
    path('medecin/rfid/login/', medecin_rfid_login, name='medecin_rfid_login'),
    path('medecin/rfid/otp/', medecin_rfid_otp, name='medecin_rfid_otp'),
    path('api/rfid-medecin-auth/', api_rfid_medecin_auth, name='api_rfid_medecin_auth'),
    
    # API RFID pour création d'utilisateur et authentification directe
    path('api/scan-rfid-user-creation/', api_scan_rfid_for_user_creation, name='api_scan_rfid_user_creation'),
    path('api/rfid-direct-auth/', api_rfid_direct_auth, name='api_rfid_direct_auth'),
    
    # Méthodes d'authentification
    path('authentification/methodes/', views.methodes_authentification, name='methodes_authentification'),

    # Sécurité HTTPS
    path('administration/securite/https/', views.https_status_view, name='https_status'),

    # Statistiques admin
    path('administration/statistiques/', views.admin_stats, name='admin_stats'),

]
urlpatterns += [
    path('api/scan-rfid/', api_scan_rfid, name='api_scan_rfid'),
    path('rfid/patient/login/', patient_rfid_login, name='patient_rfid_login'),
    path('rfid/patient/otp/', patient_rfid_otp, name='patient_rfid_otp'),
]