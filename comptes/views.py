from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.generic import View
from django.contrib.auth import logout
from django.contrib import messages
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import json
from .decorators import role_required, any_role_required, detecter_usurpation_role, verifier_elevation_privileges
from .forms import InscriptionForm, AdminCreateUserForm, RFIDCardRegisterForm
from .models import Utilisateur, Medecin, Patient, AlerteSecurite, RendezVous, HistoriqueAuthentification, LicenceAcceptation, AuditLog, RFIDCard, DossierMedical, MedecinNew, PatientNew
import logging
import requests
import uuid
import random
import string
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth.models import Group
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.signals import post_save
from comptes.keycloak_auto_sync import auto_sync_user_to_keycloak


logger = logging.getLogger(__name__)


class TestAuthView(View):
    """Vue de test pour l'authentification OIDC"""

    def get(self, request):
        return render(request, 'test_auth.html')


class HomeView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('redirection_role')
        return render(request, 'home.html')


def licence_view(request):
    """Vue pour afficher et traiter l'acceptation de la licence"""
    if request.method == 'POST':
        accept_licence = request.POST.get('accept_licence')
        confirm_age = request.POST.get('confirm_age')
        
        if accept_licence and confirm_age:
            # Stocker l'acceptation en session pour l'inscription
            request.session['licence_accepted'] = True
            request.session['licence_ip'] = request.META.get('REMOTE_ADDR', '')
            request.session['licence_user_agent'] = request.META.get('HTTP_USER_AGENT', '')
            request.session['show_licence_success'] = True
            
            return redirect('inscription')
        else:
            messages.error(request, 'Vous devez accepter la politique de confidentialité et confirmer votre âge.')
    
    return render(request, 'licence.html', {
        'title': 'Politique de Confidentialité'
    })
@require_http_methods(["POST"])
@csrf_exempt
def set_role_session(request):
    """API pour définir le rôle dans la session"""
    try:
        data = json.loads(request.body)
        role = data.get('role')
        
        if role in ['admin', 'medecin', 'patient']:
            request.session['role_tente'] = role
            return JsonResponse({'success': True, 'role': role})
        else:
            return JsonResponse({'success': False, 'error': 'Rôle invalide'})
    except Exception as e:
        logger.error(f"Erreur lors de la définition du rôle: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def redirection_role(request):
    """Redirige l'utilisateur vers son dashboard selon son rôle"""
    try:
        # Vérifier si l'utilisateur est bloqué
        if hasattr(request.user, 'est_bloque') and request.user.est_bloque:
            messages.error(request, f"Votre compte est bloqué: {request.user.raison_blocage}")
            return redirect('home')

        # Vérifier d'abord is_superuser/is_staff
        if request.user.is_superuser or request.user.is_staff:
            logger.info(f"Utilisateur staff/admin détecté: {request.user.username}")
            return redirect('admin_dashboard')

        user_groups = [group.name.lower() for group in request.user.groups.all()]
        logger.info(f"Utilisateur: {request.user.username}, Groupes: {user_groups}")

        # Vérifier et synchroniser les groupes si nécessaire
        if hasattr(request.user, 'role_autorise') and request.user.role_autorise:
            expected_groups = {
                'admin': ['admin', 'administrateurs'],
                'medecin': ['medecin', 'médecins', 'medecins'], 
                'patient': ['patient', 'patients']
            }
            
            role = request.user.role_autorise
            if role in expected_groups:
                expected = expected_groups[role]
                has_expected_group = any(group in user_groups for group in expected)
                
                if not has_expected_group:
                    logger.warning(f"Utilisateur {request.user.username} avec rôle {role} n'a pas le bon groupe. Synchronisation...")
                    sync_django_groups(request.user, role)
                    # Recharger les groupes après synchronisation
                    user_groups = [group.name.lower() for group in request.user.groups.all()]
                    logger.info(f"Groupes après synchronisation: {user_groups}")

        # Redirection selon le groupe (support anciens et nouveaux noms)
        if 'admin' in user_groups or 'administrateurs' in user_groups:
            return redirect('admin_dashboard')
        elif 'medecin' in user_groups or 'médecins' in user_groups:
            return redirect('medecin_dashboard')
        elif 'patient' in user_groups or 'patients' in user_groups:
            return redirect('patient_dashboard')

        # Si aucun rôle valide n'est trouvé
        logger.warning(f"Aucun rôle valide trouvé pour {request.user.username}")
        return redirect('default_dashboard')

    except Exception as e:
        logger.error(f"Erreur lors de la redirection: {e}")
        return redirect('default_dashboard')


@login_required
def user_info(request):
    """Retourne les informations de l'utilisateur connecté"""
    user_groups = [group.name for group in request.user.groups.all()]
    return JsonResponse({
        'username': request.user.username,
        'email': request.user.email,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'groups': user_groups,
        'is_staff': request.user.is_staff,
        'is_superuser': request.user.is_superuser,
        'est_bloque': getattr(request.user, 'est_bloque', False),
        'role_autorise': getattr(request.user, 'role_autorise', None)
    })


@role_required('admin')
def user_management(request):
    """Vue pour la gestion des utilisateurs (en attente, bloqués, tous) avec actions rapides"""
    en_attente = Utilisateur.objects.filter(role_autorise__isnull=True).order_by('-date_creation')
    bloques = Utilisateur.objects.filter(est_bloque=True).order_by('-date_blocage')
    users = Utilisateur.objects.all().order_by('-date_creation')
    return render(request, 'dashboards/user_management.html', {
        'en_attente': en_attente,
        'bloques': bloques,
        'users': users,
        'title': 'Gestion des utilisateurs',
    })


@role_required('admin')
def admin_dashboard(request):
    """Dashboard administrateur avec alertes de sécurité et compteurs dynamiques"""
    # Alertes non lues
    alertes_non_lues = AlerteSecurite.objects.filter(est_lue=False).order_by('-date_creation')[:10]
    
    # Statistiques de sécurité
    utilisateurs_bloques = Utilisateur.objects.filter(est_bloque=True).count()
    alertes_critiques = AlerteSecurite.objects.filter(niveau_urgence='CRITIQUE', est_lue=False).count()
    utilisateurs_en_attente = Utilisateur.objects.filter(role_autorise__isnull=True).count()
    alertes_non_lues_count = AlerteSecurite.objects.filter(est_lue=False).count()

    # Statistiques dynamiques
    users_count = Utilisateur.objects.count()
    medecins_count = MedecinNew.objects.count()
    patients_count = PatientNew.objects.count()
    rdv_count = RendezVous.objects.count()
    
    return render(request, 'dashboards/admin.html', {
        'user': request.user,
        'title': 'Administration',
        'alertes_non_lues': alertes_non_lues,
        'alertes_critiques': alertes_critiques,
        'utilisateurs_en_attente': utilisateurs_en_attente,
        'alertes_non_lues_count': alertes_non_lues_count,
        'utilisateurs_bloques': utilisateurs_bloques,
        'users_count': users_count,
        'medecins_count': medecins_count,
        'patients_count': patients_count,
        'rdv_count': rdv_count,
    })


@role_required('admin')
def gestion_securite(request):
    """Vue pour la gestion de la sécurité"""
    # Utilisateurs bloqués
    utilisateurs_bloques = Utilisateur.objects.filter(est_bloque=True).order_by('-date_blocage')
    
    # Utilisateurs en attente de rôle
    utilisateurs_en_attente = Utilisateur.objects.filter(role_autorise__isnull=True).order_by('-date_creation')
    
    # Alertes de sécurité
    alertes = AlerteSecurite.objects.all().order_by('-date_creation')[:50]
    
    # Historique d'authentification récent
    historique_recent = HistoriqueAuthentification.objects.filter(succes=False).order_by('-date_heure_acces')[:20]
    
    return render(request, 'admin/gestion_securite.html', {
        'utilisateurs_bloques': utilisateurs_bloques,
        'utilisateurs_en_attente': utilisateurs_en_attente,
        'alertes': alertes,
        'historique_recent': historique_recent,
        'title': 'Gestion de la Sécurité'
    })


@role_required('admin')
def debloquer_utilisateur(request, user_id):
    """Débloque un utilisateur et synchronise les rôles si nécessaire"""
    if request.method == 'POST':
        try:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            
            # Sauvegarder le rôle avant déblocage
            role_avant_deblocage = utilisateur.role_autorise
            
            # Débloquer l'utilisateur
            utilisateur.debloquer(request.user)
            
            # Si l'utilisateur a un rôle autorisé, synchroniser avec Keycloak
            if role_avant_deblocage:
                sync_success = sync_role_to_keycloak(utilisateur, role_avant_deblocage)
                if sync_success:
                    messages.success(request, f"Utilisateur {utilisateur.email} débloqué et rôle synchronisé avec Keycloak.")
                else:
                    messages.warning(request, f"Utilisateur {utilisateur.email} débloqué mais erreur de synchronisation Keycloak.")
            else:
                messages.success(request, f"Utilisateur {utilisateur.email} débloqué avec succès.")
            
            # Invalider les sessions Keycloak
            invalidate_keycloak_user_session(utilisateur.email)
            
        except Exception as e:
            logger.error(f"Erreur lors du déblocage: {e}")
            messages.error(request, f"Erreur lors du déblocage: {e}")
    
    return redirect('gestion_securite')


@role_required('admin')
def marquer_alerte_lue(request, alerte_id):
    """Marque une alerte comme lue"""
    if request.method == 'POST':
        try:
            alerte = get_object_or_404(AlerteSecurite, id=alerte_id)
            alerte.est_lue = True
            alerte.save()
            messages.success(request, "Alerte marquée comme lue.")
        except Exception as e:
            messages.error(request, f"Erreur: {e}")
    
    return redirect('gestion_securite')


def sync_role_to_keycloak(utilisateur, role):
    """
    Synchronise le rôle Django vers Keycloak
    """
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            logger.error("Impossible d'obtenir le token admin Keycloak")
            return False

        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        # 1. Rechercher l'utilisateur dans Keycloak
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={utilisateur.email}&exact=true"
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        
        if search_resp.status_code != 200 or not search_resp.json():
            logger.error(f"Utilisateur {utilisateur.email} non trouvé dans Keycloak")
            return False
        
        user_id = search_resp.json()[0]['id']

        # 2. Récupérer les rôles existants de l'utilisateur
        current_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
        current_roles_resp = requests.get(current_roles_url, headers=headers, timeout=10)
        
        if current_roles_resp.status_code != 200:
            logger.error(f"Erreur lors de la récupération des rôles actuels: {current_roles_resp.status_code}")
            return False

        current_roles = current_roles_resp.json()
        
        # 3. Récupérer tous les rôles disponibles
        all_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/roles"
        all_roles_resp = requests.get(all_roles_url, headers=headers, timeout=10)
        
        if all_roles_resp.status_code != 200:
            logger.error(f"Erreur lors de la récupération des rôles disponibles: {all_roles_resp.status_code}")
            return False

        all_roles = all_roles_resp.json()
        
        # 4. Identifier les rôles à retirer et à ajouter
        current_role_names = [role['name'] for role in current_roles]
        target_role_names = [role] if role else []
        
        # Rôles à retirer (rôles actuels qui ne sont pas dans la cible)
        roles_to_remove = [r for r in current_role_names if r in ['admin', 'medecin', 'patient'] and r not in target_role_names]
        
        # Rôles à ajouter (rôles cibles qui ne sont pas actuels)
        roles_to_add = [r for r in target_role_names if r not in current_role_names]
        
        # 5. Retirer les anciens rôles
        for role_name in roles_to_remove:
            role_to_remove = next((r for r in all_roles if r['name'] == role_name), None)
            if role_to_remove:
                remove_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
                remove_resp = requests.delete(remove_url, json=[role_to_remove], headers=headers, timeout=10)
                if remove_resp.status_code not in (204, 200):
                    logger.warning(f"Erreur lors du retrait du rôle {role_name}: {remove_resp.status_code}")
                else:
                    logger.info(f"Rôle {role_name} retiré de l'utilisateur {utilisateur.email}")

        # 6. Ajouter les nouveaux rôles
        for role_name in roles_to_add:
            role_to_add = next((r for r in all_roles if r['name'] == role_name), None)
            if role_to_add:
                add_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
                add_resp = requests.post(add_url, json=[role_to_add], headers=headers, timeout=10)
                if add_resp.status_code not in (204, 200):
                    logger.error(f"Erreur lors de l'ajout du rôle {role_name}: {add_resp.status_code} - {add_resp.text}")
                    return False
                else:
                    logger.info(f"Rôle {role_name} ajouté à l'utilisateur {utilisateur.email}")

        # 7. Invalider les sessions pour forcer la reconnexion
        sessions_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/sessions"
        sessions_resp = requests.delete(sessions_url, headers=headers, timeout=10)
        if sessions_resp.status_code == 204:
            logger.info(f"Sessions Keycloak invalidées pour {utilisateur.email}")

        # 8. Synchroniser les groupes Django
        sync_django_groups(utilisateur, role)

        logger.info(f"Synchronisation Keycloak et Django réussie pour {utilisateur.email} - Rôle: {role}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation Keycloak: {e}")
        return False


def sync_django_groups(utilisateur, role):
    """
    Synchronise les groupes Django avec le rôle attribué
    """
    try:
        # Mapping des rôles vers les groupes Django
        group_mapping = {
            'admin': 'administrateurs',
            'medecin': 'medecins',
            'patient': 'patients'
        }
        
        # Retirer l'utilisateur de tous les groupes de rôles existants
        for old_group_name in group_mapping.values():
            try:
                old_group = Group.objects.get(name=old_group_name)
                utilisateur.groups.remove(old_group)
                logger.info(f"Utilisateur {utilisateur.email} retiré du groupe {old_group_name}")
            except Group.DoesNotExist:
                pass
        
        # Ajouter l'utilisateur au nouveau groupe si le rôle est valide
        if role and role in group_mapping:
            group_name = group_mapping[role]
            try:
                group, created = Group.objects.get_or_create(name=group_name)
                utilisateur.groups.add(group)
                if created:
                    logger.info(f"Groupe {group_name} créé et utilisateur {utilisateur.email} ajouté")
                else:
                    logger.info(f"Utilisateur {utilisateur.email} ajouté au groupe {group_name}")
                return True
            except Exception as e:
                logger.error(f"Erreur lors de l'ajout au groupe {group_name}: {e}")
                return False
        
        logger.info(f"Groupes Django synchronisés pour {utilisateur.email} - Rôle: {role}")
        return True
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation des groupes Django: {e}")
        return False


@role_required('admin')
def definir_role_utilisateur(request, user_id):
    """Définit le rôle autorisé pour un utilisateur et synchronise avec Keycloak"""
    if request.method == 'POST':
        try:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            role = request.POST.get('role')
            
            if role in ['admin', 'medecin', 'patient', '']:
                # Sauvegarder l'ancien rôle pour la comparaison
                ancien_role = utilisateur.role_autorise
                
                # Mettre à jour le rôle dans Django
                utilisateur.role_autorise = role if role else None
                utilisateur.save()
                
                # Synchroniser avec Keycloak
                sync_success = sync_role_to_keycloak(utilisateur, role)
                
                # Créer une alerte
                details = f"Rôle autorisé défini à '{role}' par {request.user.email}"
                if sync_success:
                    details += " - Synchronisation Keycloak réussie"
                else:
                    details += " - Erreur de synchronisation Keycloak"
                
                AlerteSecurite.objects.create(
                    type_alerte='MODIFICATION_ROLE',
                    utilisateur_concerne=utilisateur,
                    details=details,
                    niveau_urgence='MOYENNE',
                    admin_qui_a_bloque=request.user
                )
                
                if sync_success:
                    messages.success(request, f"Rôle autorisé défini pour {utilisateur.email} et synchronisé avec Keycloak")
                else:
                    messages.warning(request, f"Rôle défini dans Django mais erreur de synchronisation Keycloak pour {utilisateur.email}")
                    
            else:
                messages.error(request, "Rôle invalide")
                
        except Exception as e:
            logger.error(f"Erreur lors de la définition du rôle: {e}")
            messages.error(request, f"Erreur: {e}")
    
    return redirect('gestion_securite')


@role_required('medecin')
def medecin_dashboard(request):
    """Dashboard médecin avec données réelles"""
    try:
        # Récupérer le profil médecin
        medecin = MedecinNew.objects.get(utilisateur=request.user)
        
        # Récupérer les rendez-vous à venir
        from datetime import date, timedelta
        from django.utils import timezone
        aujourd_hui = timezone.now().date()
        dans_7_jours = aujourd_hui + timedelta(days=7)
        
        mes_rdv_futurs = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__date__gte=aujourd_hui,
            statut__in=['EN_ATTENTE', 'CONFIRME']
        ).order_by('date_rdv')[:5]
        
        # Statistiques
        patients_suivis = PatientNew.objects.filter(
            rendez_vous__medecin=medecin
        ).distinct().count()
        
        rdv_a_venir = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__date__gte=aujourd_hui,
            statut__in=['EN_ATTENTE', 'CONFIRME']
        ).count()
        
        # Dossiers médicaux créés par ce médecin
        dossiers_crees = DossierMedical.objects.filter(
            patient__rendez_vous__medecin=medecin
        ).distinct().count()
        
        # Notifications simulées (à remplacer par un vrai système)
        notifications = []
        
        # Rendez-vous en attente de confirmation
        rdv_en_attente = RendezVous.objects.filter(
            medecin=medecin,
            statut='EN_ATTENTE'
        ).count()
        
        if rdv_en_attente > 0:
            notifications.append({
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'message': f'{rdv_en_attente} rendez-vous en attente de validation.'
            })
        
        # Nouveaux patients cette semaine
        nouveaux_patients = PatientNew.objects.filter(
            utilisateur__date_joined__gte=timezone.now() - timedelta(days=7),
            rendez_vous__medecin=medecin
        ).distinct().count()
        
        if nouveaux_patients > 0:
            notifications.append({
                'type': 'info',
                'icon': 'info-circle',
                'message': f'{nouveaux_patients} nouveau(x) patient(s) cette semaine.'
            })
        
        stats = {
            'patients_suivis': patients_suivis,
            'rdv_a_venir': rdv_a_venir,
            'dossiers_crees': dossiers_crees,
        }
        
        context = {
            'user': request.user,
            'title': 'Espace Médecin',
            'medecin': medecin,
            'mes_rdv_futurs': mes_rdv_futurs,
            'stats': stats,
            'notifications': notifications,
        }
        
    except MedecinNew.DoesNotExist:
        # Si pas de profil médecin, créer un profil basique
        stats = {
            'patients_suivis': 0,
            'rdv_a_venir': 0,
            'dossiers_crees': 0,
        }
        
        context = {
            'user': request.user,
            'title': 'Espace Médecin',
            'medecin': None,
            'mes_rdv_futurs': [],
            'stats': stats,
            'notifications': [{
                'type': 'warning',
                'icon': 'exclamation-triangle',
                'message': 'Profil médecin incomplet. Contactez l\'administrateur.'
            }],
            'profile_incomplete': True
        }
    
    return render(request, 'dashboards/medecin.html', context)


@role_required('patient')
def patient_dashboard(request):
    """Dashboard patient avec données réelles"""
    try:
        # Récupérer le profil patient
        patient = PatientNew.objects.get(utilisateur=request.user)
        
        # Récupérer les rendez-vous à venir
        from datetime import date, timedelta
        aujourd_hui = date.today()
        
        rdv_a_venir = RendezVous.objects.filter(
            patient=patient,
            date_rdv__date__gte=aujourd_hui,
            statut__in=['EN_ATTENTE', 'CONFIRME']
        ).order_by('date_rdv')[:3]
        
        # Historique des rendez-vous
        rdv_passes = RendezVous.objects.filter(
            patient=patient,
            date_rdv__date__lt=aujourd_hui
        ).order_by('-date_rdv')[:5]
        
        # Dossier médical
        try:
            dossier = DossierMedical.objects.get(patient=patient)
            derniere_consultation = rdv_passes.first()
        except DossierMedical.DoesNotExist:
            dossier = None
            derniere_consultation = None
        
        context = {
            'user': request.user,
            'title': 'Espace Patient',
            'patient': patient,
            'rdv_a_venir': rdv_a_venir,
            'rdv_passes': rdv_passes,
            'dossier': dossier,
            'derniere_consultation': derniere_consultation,
        }
        
    except PatientNew.DoesNotExist:
        # Si pas de profil patient, créer un profil basique
        context = {
            'user': request.user,
            'title': 'Espace Patient',
            'patient': None,
            'rdv_a_venir': [],
            'rdv_passes': [],
            'dossier': None,
            'derniere_consultation': None,
            'profile_incomplete': True
        }
    
    return render(request, 'dashboards/patient.html', context)


# ===== NOUVELLES VUES FONCTIONNELLES POUR LES DASHBOARDS =====

@role_required('medecin')
def liste_patients_medecin(request):
    """Liste des patients pour un médecin"""
    try:
        medecin = MedecinNew.objects.get(utilisateur=request.user)
        from django.utils import timezone
        from datetime import timedelta
        
        # Patients ayant eu des RDV avec ce médecin avec informations supplémentaires
        patients_base = PatientNew.objects.filter(
            rendez_vous__medecin=medecin
        ).distinct().order_by('utilisateur__nom')
        
        # Enrichir les données des patients
        patients_enrichis = []
        for patient in patients_base:
            # Dernière visite
            derniere_visite = RendezVous.objects.filter(
                patient=patient,
                medecin=medecin,
                statut='TERMINE'
            ).order_by('-date_rdv').first()
            
            # Prochain RDV
            prochain_rdv = RendezVous.objects.filter(
                patient=patient,
                medecin=medecin,
                date_rdv__gte=timezone.now(),
                statut__in=['EN_ATTENTE', 'CONFIRME']
            ).order_by('date_rdv').first()
            
            patient.derniere_visite = derniere_visite.date_rdv if derniere_visite else None
            patient.prochain_rdv = prochain_rdv.date_rdv if prochain_rdv else None
            patients_enrichis.append(patient)
        
        # Statistiques pour le médecin
        rdv_cette_semaine = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__gte=timezone.now(),
            date_rdv__lt=timezone.now() + timedelta(days=7)
        ).count()
        
        rdv_ce_mois = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__gte=timezone.now().replace(day=1),
            date_rdv__lt=timezone.now().replace(day=1) + timedelta(days=31)
        ).count()
        
        rdv_en_attente = RendezVous.objects.filter(
            medecin=medecin,
            statut='EN_ATTENTE'
        ).count()
        
        context = {
            'patients': patients_enrichis,
            'medecin': medecin,
            'title': 'Mes Patients',
            'rdv_cette_semaine': rdv_cette_semaine,
            'rdv_ce_mois': rdv_ce_mois,
            'rdv_en_attente': rdv_en_attente,
        }
        return render(request, 'dashboards/liste_patients_medecin.html', context)
    except MedecinNew.DoesNotExist:
        messages.error(request, "Profil médecin non trouvé")
        return redirect('medecin_dashboard')


@role_required('medecin')
def calendrier_medecin(request):
    """Calendrier des rendez-vous pour un médecin"""
    try:
        medecin = MedecinNew.objects.get(utilisateur=request.user)
        
        # Récupération des paramètres de filtrage
        statut_filtre = request.GET.get('statut', 'all')
        
        # Récupérer les rendez-vous du mois avec pagination
        from django.utils import timezone
        from datetime import date, timedelta
        from django.core.paginator import Paginator
        
        aujourd_hui = timezone.now().date()
        
        # Récupérer tous les rendez-vous du médecin
        rdv_queryset = RendezVous.objects.filter(medecin=medecin)
        
        # Appliquer le filtre de statut
        if statut_filtre != 'all':
            rdv_queryset = rdv_queryset.filter(statut=statut_filtre)
        
        rdv_queryset = rdv_queryset.order_by('-date_rdv')
        
        # Pagination
        paginator = Paginator(rdv_queryset, 10)
        page_number = request.GET.get('page')
        rdv_page = paginator.get_page(page_number)
        
        # Séparer les rendez-vous par catégorie
        rdv_aujourd_hui = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__date=aujourd_hui
        ).order_by('date_rdv')
        
        rdv_a_venir = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__date__gt=aujourd_hui,
            statut__in=['EN_ATTENTE', 'CONFIRME']
        ).order_by('date_rdv')[:5]
        
        rdv_passes = RendezVous.objects.filter(
            medecin=medecin,
            date_rdv__date__lt=aujourd_hui
        ).order_by('-date_rdv')[:5]
        
        # Statistiques
        stats = {
            'total': RendezVous.objects.filter(medecin=medecin).count(),
            'en_attente': RendezVous.objects.filter(medecin=medecin, statut='EN_ATTENTE').count(),
            'confirmes': RendezVous.objects.filter(medecin=medecin, statut='CONFIRME').count(),
            'termines': RendezVous.objects.filter(medecin=medecin, statut='TERMINE').count(),
            'annules': RendezVous.objects.filter(medecin=medecin, statut='ANNULE').count(),
        }
        
        context = {
            'rdv_page': rdv_page,
            'rdv_aujourd_hui': rdv_aujourd_hui,
            'rdv_a_venir': rdv_a_venir,
            'rdv_passes': rdv_passes,
            'medecin': medecin,
            'title': 'Mon Calendrier',
            'statut_filtre': statut_filtre,
            'stats': stats,
        }
        return render(request, 'dashboards/calendrier_medecin.html', context)
    except MedecinNew.DoesNotExist:
        messages.error(request, "Profil médecin non trouvé")
        return redirect('medecin_dashboard')


@role_required('medecin')
def confirmer_rdv_medecin(request, rdv_id):
    """Confirmer un rendez-vous"""
    if request.method == 'POST':
        try:
            medecin = MedecinNew.objects.get(utilisateur=request.user)
            rdv = RendezVous.objects.get(id=rdv_id, medecin=medecin)
            
            rdv.statut = 'CONFIRME'
            rdv.save()
            
            return JsonResponse({'success': True, 'message': 'Rendez-vous confirmé'})
        except (MedecinNew.DoesNotExist, RendezVous.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Rendez-vous non trouvé'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@role_required('medecin')
def annuler_rdv_medecin(request, rdv_id):
    """Annuler un rendez-vous"""
    if request.method == 'POST':
        try:
            medecin = MedecinNew.objects.get(utilisateur=request.user)
            rdv = RendezVous.objects.get(id=rdv_id, medecin=medecin)
            
            rdv.statut = 'ANNULE'
            rdv.save()
            
            return JsonResponse({'success': True, 'message': 'Rendez-vous annulé'})
        except (MedecinNew.DoesNotExist, RendezVous.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Rendez-vous non trouvé'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@role_required('medecin')
def terminer_rdv_medecin(request, rdv_id):
    """Terminer un rendez-vous"""
    if request.method == 'POST':
        try:
            medecin = MedecinNew.objects.get(utilisateur=request.user)
            rdv = RendezVous.objects.get(id=rdv_id, medecin=medecin)
            
            rdv.statut = 'TERMINE'
            rdv.save()
            
            return JsonResponse({'success': True, 'message': 'Rendez-vous terminé'})
        except (MedecinNew.DoesNotExist, RendezVous.DoesNotExist):
            return JsonResponse({'success': False, 'message': 'Rendez-vous non trouvé'})
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@role_required('patient')
def prendre_rdv(request):
    """Prise de rendez-vous pour un patient"""
    try:
        patient = PatientNew.objects.get(utilisateur=request.user)
        
        if request.method == 'POST':
            medecin_id = request.POST.get('medecin_id')
            date_rdv = request.POST.get('date_rdv')
            heure_rdv = request.POST.get('heure_rdv')
            motif = request.POST.get('motif', '')
            
            try:
                medecin = MedecinNew.objects.get(id=medecin_id)
                from datetime import datetime
                from django.utils import timezone
                
                # Construire la date complète
                date_heure_str = f"{date_rdv} {heure_rdv}"
                date_heure_naive = datetime.strptime(date_heure_str, "%Y-%m-%d %H:%M")
                date_heure = timezone.make_aware(date_heure_naive)
                
                # Vérifier que la date n'est pas dans le passé
                if date_heure < timezone.now():
                    messages.error(request, "Impossible de prendre un rendez-vous dans le passé")
                else:
                    # Vérifier disponibilité (créneau de 30 minutes)
                    rdv_existant = RendezVous.objects.filter(
                        medecin=medecin,
                        date_rdv__date=date_heure.date(),
                        date_rdv__hour=date_heure.hour,
                        date_rdv__minute__range=[date_heure.minute-29, date_heure.minute+29]
                    ).exists()
                    
                    if not rdv_existant:
                        rdv = RendezVous.objects.create(
                            patient=patient,
                            medecin=medecin,
                            date_rdv=date_heure,
                            motif=motif,
                            statut='EN_ATTENTE'
                        )
                        messages.success(request, f"Rendez-vous demandé avec succès pour le {date_heure.strftime('%d/%m/%Y à %H:%M')} avec Dr. {medecin.utilisateur.nom}")
                        return redirect('patient_dashboard')
                    else:
                        messages.error(request, "Ce créneau horaire n'est pas disponible")
                        
            except MedecinNew.DoesNotExist:
                messages.error(request, "Médecin sélectionné introuvable")
            except ValueError as e:
                messages.error(request, "Format de date ou heure invalide")
            except Exception as e:
                messages.error(request, f"Erreur lors de la prise de rendez-vous: {e}")
        
        # Préparer les données pour le template
        from datetime import date, timedelta
        date_min = date.today().strftime('%Y-%m-%d')
        date_max = (date.today() + timedelta(days=90)).strftime('%Y-%m-%d')  # 3 mois à l'avance
        
        # Liste des médecins disponibles avec leurs spécialités
        medecins = MedecinNew.objects.select_related('utilisateur').prefetch_related('specialites').order_by('utilisateur__nom')
        
        context = {
            'medecins': medecins,
            'patient': patient,
            'date_min': date_min,
            'date_max': date_max,
            'title': 'Prendre un Rendez-vous'
        }
        return render(request, 'dashboards/prendre_rdv.html', context)
    except PatientNew.DoesNotExist:
        messages.error(request, "Profil patient non trouvé")
        return redirect('patient_dashboard')


@role_required('patient')
def mon_dossier_medical(request):
    """Consultation du dossier médical par le patient"""
    try:
        patient = PatientNew.objects.get(utilisateur=request.user)
        
        try:
            dossier = DossierMedical.objects.get(patient=patient)
        except DossierMedical.DoesNotExist:
            dossier = None
        
        # Historique des consultations (via rendez-vous)
        consultations = RendezVous.objects.filter(
            patient=patient,
            statut='TERMINE'
        ).order_by('-date_rdv')
        
        context = {
            'patient': patient,
            'dossier': dossier,
            'consultations': consultations,
            'title': 'Mon Dossier Médical'
        }
        return render(request, 'dashboards/mon_dossier_medical.html', context)
    except PatientNew.DoesNotExist:
        messages.error(request, "Profil patient non trouvé")
        return redirect('patient_dashboard')


@role_required('patient')
def historique_rdv_patient(request):
    """Historique complet des rendez-vous pour un patient"""
    try:
        patient = PatientNew.objects.get(utilisateur=request.user)
        
        # Tous les rendez-vous du patient
        rdv_tous = RendezVous.objects.filter(patient=patient).order_by('-date_rdv')
        
        # Filtrage par statut
        statut_filtre = request.GET.get('statut', 'tous')
        if statut_filtre != 'tous':
            rdv_tous = rdv_tous.filter(statut=statut_filtre)
        
        # Pagination
        from django.core.paginator import Paginator
        paginator = Paginator(rdv_tous, 10)  # 10 rendez-vous par page
        page_number = request.GET.get('page')
        rdv_page = paginator.get_page(page_number)
        
        # Statistiques
        stats = {
            'total': RendezVous.objects.filter(patient=patient).count(),
            'en_attente': RendezVous.objects.filter(patient=patient, statut='EN_ATTENTE').count(),
            'confirme': RendezVous.objects.filter(patient=patient, statut='CONFIRME').count(),
            'termine': RendezVous.objects.filter(patient=patient, statut='TERMINE').count(),
            'annule': RendezVous.objects.filter(patient=patient, statut='ANNULE').count(),
        }
        
        context = {
            'patient': patient,
            'rdv_page': rdv_page,
            'stats': stats,
            'statut_filtre': statut_filtre,
            'title': 'Historique des Rendez-vous'
        }
        return render(request, 'dashboards/historique_rdv.html', context)
    except PatientNew.DoesNotExist:
        messages.error(request, "Profil patient non trouvé")
        return redirect('patient_dashboard')


@role_required('patient')
def annuler_rdv_patient(request, rdv_id):
    """Annulation d'un rendez-vous par le patient"""
    if request.method == 'POST':
        try:
            patient = PatientNew.objects.get(utilisateur=request.user)
            rdv = get_object_or_404(RendezVous, id=rdv_id, patient=patient)
            
            # Vérifier que le rendez-vous peut être annulé
            if rdv.statut in ['EN_ATTENTE', 'CONFIRME']:
                rdv.statut = 'ANNULE'
                rdv.save()
                
                # Créer une notification pour le médecin (optionnel)
                from django.utils import timezone
                logger.info(f"Rendez-vous {rdv_id} annulé par le patient {patient.utilisateur.email}")
                
                return JsonResponse({
                    'success': True,
                    'message': 'Rendez-vous annulé avec succès'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Ce rendez-vous ne peut pas être annulé'
                })
                
        except PatientNew.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Profil patient introuvable'
            })
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation du RDV {rdv_id}: {e}")
            return JsonResponse({
                'success': False,
                'message': 'Erreur lors de l\'annulation'
            })
    
    return JsonResponse({'success': False, 'message': 'Méthode non autorisée'})


@role_required('admin')
def statistiques_detaillees(request):
    """Statistiques détaillées pour l'administrateur"""
    from datetime import date, timedelta
    from django.db.models import Count, Q
    
    # Statistiques générales
    stats = {
        'total_utilisateurs': Utilisateur.objects.count(),
        'total_medecins': MedecinNew.objects.count(),
        'total_patients': PatientNew.objects.count(),
        'total_rdv': RendezVous.objects.count(),
        'rdv_cette_semaine': RendezVous.objects.filter(
            date_rdv__date__range=[
                date.today(),
                date.today() + timedelta(days=7)
            ]
        ).count(),
        'utilisateurs_actifs_30j': Utilisateur.objects.filter(
            date_derniere_connexion__gte=date.today() - timedelta(days=30)
        ).count(),
        'alertes_non_resolues': AlerteSecurite.objects.filter(est_lue=False).count(),
    }
    
    # Répartition par rôle
    repartition_roles = Utilisateur.objects.values('role_autorise').annotate(
        count=Count('id')
    ).order_by('role_autorise')
    
    # Évolution des inscriptions (derniers 30 jours)
    evolution_inscriptions = []
    for i in range(30):
        jour = date.today() - timedelta(days=i)
        count = Utilisateur.objects.filter(date_creation__date=jour).count()
        evolution_inscriptions.append({
            'date': jour,
            'count': count
        })
    
    context = {
        'stats': stats,
        'repartition_roles': repartition_roles,
        'evolution_inscriptions': reversed(evolution_inscriptions),
        'title': 'Statistiques Détaillées'
    }
    return render(request, 'dashboards/admin_stats.html', context)


@role_required('medecin')
def creer_dossier_medical(request):
    """Création d'un nouveau dossier médical"""
    try:
        medecin = MedecinNew.objects.get(utilisateur=request.user)
        
        if request.method == 'POST':
            patient_id = request.POST.get('patient_id')
            resume = request.POST.get('resume')
            antecedents = request.POST.get('antecedents', '')
            traitement_actuel = request.POST.get('traitement_actuel', '')
            groupe_sanguin = request.POST.get('groupe_sanguin', '')
            statut = request.POST.get('statut', 'actif')
            
            try:
                patient = PatientNew.objects.get(id=patient_id)
                
                # Vérifier si le dossier existe déjà
                dossier, created = DossierMedical.objects.get_or_create(
                    patient=patient,
                    defaults={
                        'notes_importantes': resume,
                        'statut': statut
                    }
                )
                
                if created:
                    messages.success(request, f"Dossier médical créé pour {patient.utilisateur.prenom} {patient.utilisateur.nom}")
                else:
                    # Mettre à jour le dossier existant
                    dossier.notes_importantes = resume
                    dossier.statut = statut
                    dossier.save()
                    messages.info(request, f"Dossier médical mis à jour pour {patient.utilisateur.prenom} {patient.utilisateur.nom}")
                
                return redirect('liste_patients_medecin')
            except PatientNew.DoesNotExist:
                messages.error(request, "Patient non trouvé")
        
        # Liste des patients pour ce médecin
        patients = PatientNew.objects.filter(
            rendez_vous__medecin=medecin
        ).distinct().order_by('utilisateur__nom')
        
        # Derniers dossiers créés
        dossiers_recents = DossierMedical.objects.filter(
            patient__rendez_vous__medecin=medecin
        ).distinct().order_by('-date_creation')[:5]
        
        context = {
            'patients': patients,
            'medecin': medecin,
            'title': 'Créer un Dossier Médical',
            'dossiers_recents': dossiers_recents,
        }
        return render(request, 'dashboards/creer_dossier.html', context)
    except MedecinNew.DoesNotExist:
        messages.error(request, "Profil médecin non trouvé")
        return redirect('medecin_dashboard')


@login_required
def default_dashboard(request):
    """Dashboard par défaut"""
    return render(request, 'dashboards/default.html', {
        'user': request.user,
        'title': 'Tableau de bord'
    })


@any_role_required('admin', 'medecin', 'patient')
def profile_view(request):
    """Page de profil utilisateur"""
    return render(request, 'profile.html', {
        'user': request.user,
        'title': 'Mon Profil'
    })


def custom_logout(request):
    """Déconnexion personnalisée avec nettoyage complet"""
    try:
        # 1. Préparation des données avant déconnexion
        username = request.user.username if request.user.is_authenticated else None
        oidc_id_token = request.session.get('oidc_id_token')

        # 2. Déconnexion Django
        logout(request)

        # 3. Nettoyage complet
        request.session.flush()
        response = redirect('home')

        # 4. Suppression des cookies
        cookies_to_delete = [
            'sessionid',
            'csrftoken',
            'oidc_access_token',
            'oidc_refresh_token',
            'oidc_id_token'
        ]
        for cookie in cookies_to_delete:
            response.delete_cookie(cookie)
            response.delete_cookie(cookie, domain=settings.SESSION_COOKIE_DOMAIN)

        # 5. Déconnexion Keycloak côté client
        if oidc_id_token and hasattr(settings, 'OIDC_OP_LOGOUT_URL'):
            params = {
                'id_token_hint': oidc_id_token,
                'post_logout_redirect_uri': request.build_absolute_uri('/')
            }
            return redirect(f"{settings.OIDC_OP_LOGOUT_URL}?{urlencode(params)}")

        return response

    except Exception as e:
        logger.error(f"Erreur déconnexion: {e}")
        try:
            request.session.flush()
        except:
            pass
        return redirect('home')


def invalidate_keycloak_user_session(username, access_token=None):
    """Invalide les sessions Keycloak via l'API Admin"""
    try:
        keycloak_url = getattr(settings, 'OIDC_OP_BASE_URL', 'http://localhost:8080')
        realm = getattr(settings, 'OIDC_REALM', 'KeurDoctorSecure')

        # 1. Obtenir un token admin
        admin_token = get_keycloak_admin_token(keycloak_url)
        if not admin_token:
            logger.warning("Impossible d'obtenir le token admin Keycloak")
            return False

        # 2. Rechercher l'utilisateur
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        search_url = f"{keycloak_url}/admin/realms/{realm}/users?username={username}&exact=true"
        response = requests.get(search_url, headers=headers, timeout=5)

        if response.status_code != 200 or not response.json():
            logger.warning(f"Utilisateur {username} non trouvé dans Keycloak")
            return False

        user_id = response.json()[0]['id']

        # 3. Supprimer les sessions
        sessions_url = f"{keycloak_url}/admin/realms/{realm}/users/{user_id}/sessions"
        sessions_response = requests.delete(sessions_url, headers=headers, timeout=5)

        if sessions_response.status_code == 204:
            logger.info(f"Sessions Keycloak invalidées pour {username}")
            return True

        logger.warning(f"Erreur lors de l'invalidation des sessions: {sessions_response.status_code}")
        return False

    except Exception as e:
        logger.error(f"Erreur lors de l'invalidation des sessions Keycloak: {e}")
        return False


def get_keycloak_admin_token(keycloak_url):
    """Obtenir un token admin Keycloak"""
    try:
        url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
        data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': getattr(settings, 'KEYCLOAK_ADMIN_USER', 'admin'),
            'password': getattr(settings, 'KEYCLOAK_ADMIN_PASSWORD', 'admin')
        }

        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            return response.json()['access_token']

        logger.warning(f"Erreur d'authentification admin: {response.status_code}")
        return None

    except Exception as e:
        logger.error(f"Erreur lors de l'obtention du token admin: {e}")
        return None

def inscription_view(request):
    """Vue pour l'inscription des nouveaux utilisateurs"""
    # Vérifier si la licence a été acceptée
    if not request.session.get('licence_accepted'):
        return redirect('licence')
    
    # Système de filtrage simple : vider tous les messages sauf ceux autorisés
    storage = messages.get_messages(request)
    # Consommer tous les messages existants
    list(storage)  # Ceci vide le storage
    
    # Ajouter uniquement le message de licence acceptée si nécessaire
    if request.session.get('show_licence_success'):
        messages.success(request, 'Licence acceptée. Vous pouvez maintenant procéder à votre inscription.')
        del request.session['show_licence_success']
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            try:
                # Récupérer les données du formulaire
                email = form.cleaned_data['email']
                prenom = form.cleaned_data['prenom']
                nom = form.cleaned_data['nom']
                role = form.cleaned_data['role']
                
                # Générer un UUID pour Keycloak
                keycloak_id = uuid.uuid4()
                
                # Créer l'utilisateur dans Django (sans rôle autorisé)
                utilisateur = Utilisateur.objects.create(
                    email=email,
                    prenom=prenom,
                    nom=nom,
                    keycloak_id=keycloak_id,
                    is_active=True,
                    role_autorise=None,  # Laisser à None, l'admin devra l'attribuer
                    role_demande=role   # Remplir le rôle souhaité
                )
                
                # Enregistrer l'acceptation de la licence
                LicenceAcceptation.objects.create(
                    utilisateur=utilisateur,
                    type_licence='POLITIQUE_CONFIDENTIALITE',
                    version='1.0',
                    ip_adresse=request.session.get('licence_ip', ''),
                    user_agent=request.session.get('licence_user_agent', '')
                )
                
                # Créer une alerte pour l'admin
                AlerteSecurite.objects.create(
                    type_alerte='NOUVEL_UTILISATEUR_EN_ATTENTE',
                    utilisateur_concerne=utilisateur,
                    details=f"Nouvel utilisateur inscrit : {utilisateur.email}. Rôle à attribuer. Licence acceptée.",
                    niveau_urgence='MOYENNE'
                )
                
                # Créer l'utilisateur dans Keycloak
                if create_keycloak_user(utilisateur, role):
                    # Créer le profil spécifique selon le rôle (optionnel, car pas encore autorisé)
                    if role == 'medecin':
                        medecin = MedecinNew.objects.create(
                            utilisateur=utilisateur,
                            numero_ordre=form.cleaned_data.get('numero_praticien', 'NON_RENSEIGNE'),
                        )
                        # Ajouter la spécialité si fournie
                        specialite_nom = form.cleaned_data.get('specialite')
                        if specialite_nom:
                            try:
                                from comptes.models import SpecialiteMedicale
                                specialite, created = SpecialiteMedicale.objects.get_or_create(
                                    nom=specialite_nom.strip(),
                                    defaults={'description': f'Spécialité: {specialite_nom}'}
                                )
                                medecin.specialites.add(specialite)
                            except Exception as e:
                                logger.error(f"Erreur lors de l'ajout de la spécialité: {e}")
                    elif role == 'patient':
                        # Générer un numéro de dossier unique
                        numero_dossier = form.cleaned_data['numero_dossier']
                        if numero_dossier:
                            # Vérifier si le numéro existe déjà
                            counter = 1
                            original_numero = numero_dossier
                            while PatientNew.objects.filter(numero_securite_sociale=numero_dossier).exists():
                                numero_dossier = f"{original_numero}_{counter}"
                                counter += 1
                        else:
                            # Générer un numéro automatique si aucun n'est fourni
                            import random
                            numero_dossier = f"P{random.randint(1000, 9999)}"
                            while PatientNew.objects.filter(numero_securite_sociale=numero_dossier).exists():
                                numero_dossier = f"P{random.randint(1000, 9999)}"
                        
                        PatientNew.objects.create(
                            utilisateur=utilisateur,
                            date_naissance=form.cleaned_data['date_naissance'],
                            numero_securite_sociale=numero_dossier  # Utiliser numero_dossier comme numero_securite_sociale temporairement
                        )
                    
                    # Nettoyer la session
                    del request.session['licence_accepted']
                    del request.session['licence_ip']
                    del request.session['licence_user_agent']
                    messages.success(request, f'Inscription réussie ! Votre compte a été créé et est en attente de validation par un administrateur.')
                    # Marquer ce message comme autorisé pour la page d'accueil
                    request.session['inscription_success_message'] = True
                    return redirect('home')
                else:
                    # Si Keycloak échoue, supprimer l'utilisateur Django
                    utilisateur.delete()
                    messages.error(request, 'Erreur lors de la création du compte. Veuillez réessayer.')
                    
            except Exception as e:
                logger.error(f"Erreur lors de l'inscription: {e}")
                messages.error(request, 'Une erreur est survenue lors de l\'inscription.')
    else:
        form = InscriptionForm()
    
    return render(request, 'inscription.html', {
        'form': form,
        'title': 'Inscription'
    })

def create_keycloak_user_with_role(utilisateur, role, password):
    """
    Crée ou met à jour un utilisateur dans Keycloak avec le rôle approprié et le mot de passe fourni
    """
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            logger.error("Impossible d'obtenir le token admin Keycloak")
            return False

        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        # Vérifier si l'utilisateur existe déjà dans Keycloak
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?username={utilisateur.email}"
        search_resp = requests.get(search_url, headers=headers)
        
        user_exists = False
        user_id = None
        
        if search_resp.status_code == 200 and search_resp.json():
            # L'utilisateur existe déjà, on le met à jour
            user_id = search_resp.json()[0]['id']
            user_exists = True
            logger.info(f"Utilisateur {utilisateur.email} existe déjà dans Keycloak, mise à jour...")
            
            # Données de mise à jour
            update_data = {
                "firstName": utilisateur.prenom,
                "lastName": utilisateur.nom,
                "enabled": True,
                "emailVerified": True,
                "attributes": {
                    "keycloak_id": [str(utilisateur.keycloak_id)],
                    "role": [role]
                }
            }
            
            # Mettre à jour l'utilisateur
            update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
            update_resp = requests.put(update_url, json=update_data, headers=headers)
            
            if update_resp.status_code not in (204, 200):
                logger.error(f"Erreur mise à jour Keycloak: {update_resp.status_code} - {update_resp.text}")
                return False
                
            logger.info(f"Utilisateur {utilisateur.email} mis à jour dans Keycloak")
        
        if not user_exists:
            # L'utilisateur n'existe pas, on le crée
            logger.info(f"Création de l'utilisateur {utilisateur.email} dans Keycloak...")
            
            user_data = {
                "username": utilisateur.email,
                "email": utilisateur.email,
                "firstName": utilisateur.prenom,
                "lastName": utilisateur.nom,
                "enabled": True,
                "emailVerified": True,
                "attributes": {
                    "keycloak_id": [str(utilisateur.keycloak_id)],
                    "role": [role]
                }
            }
                    
            url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
            response = requests.post(url, json=user_data, headers=headers, timeout=10)
                    
            if response.status_code == 409:
                # Conflit - l'utilisateur existe déjà, essayer de le récupérer
                logger.warning(f"Conflit détecté pour {utilisateur.email}, tentative de récupération...")
                search_resp2 = requests.get(search_url, headers=headers)
                if search_resp2.status_code == 200 and search_resp2.json():
                    user_id = search_resp2.json()[0]['id']
                    user_exists = True
                    logger.info(f"Utilisateur {utilisateur.email} récupéré après conflit")
                else:
                    logger.error(f"Impossible de récupérer l'utilisateur après conflit: {utilisateur.email}")
                    return False
            elif response.status_code != 201:
                logger.error(f"Erreur création Keycloak: {response.status_code} - {response.text}")
                return False
            else:
                # Récupérer l'ID de l'utilisateur créé
                search_resp = requests.get(search_url, headers=headers)
                if search_resp.status_code != 200 or not search_resp.json():
                    logger.error("Utilisateur créé mais impossible de le retrouver pour l'affectation du mot de passe/groupe.")
                    return False
                user_id = search_resp.json()[0]['id']
                logger.info(f"Utilisateur {utilisateur.email} créé dans Keycloak")

        # Définir le mot de passe fourni (pour les utilisateurs nouveaux et existants)
        if user_id:
            password_payload = {
                "type": "password",
                "value": password,
                "temporary": True  # L'utilisateur devra changer son mot de passe à la première connexion
            }
            pwd_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/reset-password"
            pwd_resp = requests.put(pwd_url, json=password_payload, headers=headers)
            if pwd_resp.status_code not in (204, 200):
                logger.error(f"Erreur lors de l'affectation du mot de passe: {pwd_resp.status_code} - {pwd_resp.text}")
                return False

            # Ajouter l'utilisateur au groupe approprié
            group_mapping = {
                'admin': 'administrateurs',
                'medecin': 'medecins', 
                'patient': 'patients'
            }
            group_name = group_mapping.get(role, role)
            
            logger.info(f"[SYNC] Tentative d'ajout de {utilisateur.email} au groupe '{group_name}' dans Keycloak")
            
            # Chercher l'ID du groupe
            group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
            group_resp = requests.get(group_url, headers=headers)
            
            if group_resp.status_code == 200:
                groups = group_resp.json()
                logger.info(f"Groupes disponibles dans Keycloak: {[g['name'] for g in groups]}")
                
                group_id = next((g['id'] for g in groups if g['name'] == group_name), None)
                
                if group_id:
                    logger.info(f"Groupe '{group_name}' trouvé avec ID: {group_id}")
                    
                    # Vérifier si l'utilisateur est déjà dans le groupe
                    user_groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups"
                    user_groups_resp = requests.get(user_groups_url, headers=headers)
                    
                    if user_groups_resp.status_code == 200:
                        user_groups = user_groups_resp.json()
                        user_group_names = [g['name'] for g in user_groups]
                        logger.info(f"Groupes actuels de {utilisateur.email}: {user_group_names}")
                        
                        if group_name not in user_group_names:
                            # Ajouter l'utilisateur au groupe
                            add_group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups/{group_id}"
                            add_group_resp = requests.put(add_group_url, headers=headers)

                            if add_group_resp.status_code in (204, 200):
                                logger.info(f"[SYNC] Utilisateur {utilisateur.email} ajouté au groupe {group_name} dans Keycloak")
                            else:
                                logger.error(f"[SYNC] Erreur lors de l'ajout au groupe: {add_group_resp.status_code} - {add_group_resp.text}")
                        else:
                            logger.info(f"[SYNC] Utilisateur {utilisateur.email} est déjà dans le groupe {group_name}")
                    else:
                        logger.error(f"[SYNC] Erreur lors de la récupération des groupes de l'utilisateur: {user_groups_resp.status_code}")
                else:
                    logger.warning(f"[SYNC] Groupe '{group_name}' introuvable dans Keycloak. Groupes disponibles: {[g['name'] for g in groups]}")
                    
                    # Essayer de créer le groupe s'il n'existe pas
                    logger.info(f"Tentative de création du groupe '{group_name}'...")
                    create_group_data = {
                        "name": group_name,
                        "attributes": {
                            "description": [f"Groupe pour les {group_name}"]
                        }
                    }
                    create_group_resp = requests.post(group_url, json=create_group_data, headers=headers)
                    
                    if create_group_resp.status_code in (201, 409):  # 409 = groupe existe déjà
                        logger.info(f"[SYNC] Groupe '{group_name}' créé ou existe déjà")
                        
                        # Récupérer l'ID du groupe nouvellement créé
                        group_resp2 = requests.get(group_url, headers=headers)
                        if group_resp2.status_code == 200:
                            groups2 = group_resp2.json()
                            group_id2 = next((g['id'] for g in groups2 if g['name'] == group_name), None)
                            
                            if group_id2:
                                add_group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups/{group_id2}"
                                add_group_resp = requests.put(add_group_url, headers=headers)
                                
                                if add_group_resp.status_code in (204, 200):
                                    logger.info(f"[SYNC] Utilisateur {utilisateur.email} ajouté au groupe {group_name} nouvellement créé")
                                else:
                                    logger.error(f"[SYNC] Erreur lors de l'ajout au groupe nouvellement créé: {add_group_resp.status_code}")
                            else:
                                logger.error(f"[SYNC] Impossible de récupérer l'ID du groupe '{group_name}' nouvellement créé")
                        else:
                            logger.error(f"[SYNC] Erreur lors de la récupération des groupes après création: {group_resp2.status_code}")
                    else:
                        logger.error(f"[SYNC] Erreur lors de la création du groupe: {create_group_resp.status_code} - {create_group_resp.text}")
            else:
                logger.error(f"[SYNC] Impossible de récupérer la liste des groupes Keycloak: {group_resp.status_code} - {group_resp.text}")

            # Attribuer le rôle Keycloak (realm role) à l'utilisateur
            role_mapping = {
                'admin': 'admin',
                'medecin': 'medecin',
                'patient': 'patient'
            }
            role_name = role_mapping.get(role)
            if role_name:
                # 1. Récupérer l'ID du rôle
                roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/roles/{role_name}"
                role_resp = requests.get(roles_url, headers=headers)
                if role_resp.status_code == 200:
                    role_data = role_resp.json()
                    role_id = role_data['id']
                    # 2. Attribuer le rôle à l'utilisateur
                    assign_role_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
                    payload = [{
                        "id": role_id,
                        "name": role_name
                    }]
                    assign_resp = requests.post(assign_role_url, json=payload, headers=headers)
                    if assign_resp.status_code in (204, 200):
                        logger.info(f"[SYNC] Rôle '{role_name}' attribué à {utilisateur.email} dans Keycloak")
                    else:
                        logger.error(f"[SYNC] Erreur lors de l'attribution du rôle: {assign_resp.status_code} - {assign_resp.text}")
                else:
                    logger.error(f"[SYNC] Impossible de récupérer le rôle '{role_name}' dans Keycloak: {role_resp.status_code}")

        logger.info(f"Utilisateur {utilisateur.email} synchronisé avec succès dans Keycloak avec le rôle {role}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation Keycloak: {e}")
        return False

def create_keycloak_user(utilisateur, role):
    """
    Fonction legacy - utilise create_keycloak_user_with_role avec un mot de passe par défaut
    """
    return create_keycloak_user_with_role(utilisateur, role, "ChangeMe123!")

def ajouter_utilisateur_dans_groupe_django(utilisateur):
    """
    Fonction legacy - utilise maintenant sync_django_groups
    """
    return sync_django_groups(utilisateur, utilisateur.role_autorise)

@role_required('admin')
def synchroniser_utilisateur_keycloak(request, user_id):
    """Synchronise manuellement un utilisateur avec Keycloak"""
    if request.method == 'POST':
        try:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            
            # Synchroniser le rôle actuel
            if utilisateur.role_autorise:
                # Générer un mot de passe temporaire pour la synchronisation
                import secrets
                import string
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                
                sync_success = create_keycloak_user_with_role(utilisateur, utilisateur.role_autorise, temp_password)
                
                if sync_success:
                    messages.success(request, f"✅ Utilisateur {utilisateur.email} synchronisé avec Keycloak (rôle: {utilisateur.role_autorise})")
                    logger.info(f"Utilisateur {utilisateur.email} synchronisé avec Keycloak")
                else:
                    messages.error(request, f"❌ Erreur lors de la synchronisation de {utilisateur.email} avec Keycloak")
                    logger.error(f"Échec de la synchronisation Keycloak pour {utilisateur.email}")
            else:
                messages.warning(request, f"⚠️ Utilisateur {utilisateur.email} n'a pas de rôle autorisé à synchroniser")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {e}")
            messages.error(request, f"❌ Erreur lors de la synchronisation: {e}")
    
    return redirect('gestion_securite')

@role_required('admin')
def synchroniser_tous_utilisateurs_keycloak(request):
    """Synchronise tous les utilisateurs Django avec Keycloak"""
    if request.method == 'POST':
        try:
            utilisateurs = Utilisateur.objects.filter(role_autorise__isnull=False)
            succes_count = 0
            echec_count = 0
            
            for utilisateur in utilisateurs:
                try:
                    # Générer un mot de passe temporaire
                    import secrets
                    import string
                    temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                    
                    sync_success = create_keycloak_user_with_role(utilisateur, utilisateur.role_autorise, temp_password)
                    
                    # Synchroniser aussi les groupes Django
                    django_sync_success = sync_django_groups(utilisateur, utilisateur.role_autorise)
                    
                    if sync_success and django_sync_success:
                        succes_count += 1
                        logger.info(f"Utilisateur {utilisateur.email} synchronisé avec Keycloak et groupes Django")
                    else:
                        echec_count += 1
                        logger.error(f"Échec de la synchronisation pour {utilisateur.email} (Keycloak: {sync_success}, Django: {django_sync_success})")
                        
                except Exception as e:
                    echec_count += 1
                    logger.error(f"Erreur lors de la synchronisation de {utilisateur.email}: {e}")
            
            if echec_count == 0:
                messages.success(request, f"✅ Synchronisation réussie : {succes_count} utilisateurs synchronisés avec Keycloak")
            else:
                messages.warning(request, f"⚠️ Synchronisation partielle : {succes_count} succès, {echec_count} échecs")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation globale: {e}")
            messages.error(request, f"❌ Erreur lors de la synchronisation globale: {e}")
    
    return redirect('gestion_securite')

@role_required('admin')
def synchroniser_groupes_django_tous(request):
    """Synchronise les groupes Django pour tous les utilisateurs ayant un rôle"""
    if request.method == 'POST':
        try:
            utilisateurs = Utilisateur.objects.filter(role_autorise__isnull=False)
            success_count = 0
            error_count = 0
            
            for utilisateur in utilisateurs:
                try:
                    if sync_django_groups(utilisateur, utilisateur.role_autorise):
                        success_count += 1
                        logger.info(f"✅ Groupes Django synchronisés: {utilisateur.email}")
                    else:
                        error_count += 1
                        logger.error(f"❌ Erreur groupes Django: {utilisateur.email}")
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Erreur pour {utilisateur.email}: {e}")
            
            if error_count == 0:
                messages.success(request, f"✅ Groupes Django synchronisés pour {success_count} utilisateurs")
            else:
                messages.warning(request, f"⚠️ Groupes Django: {success_count} réussies, {error_count} erreurs")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des groupes: {e}")
            messages.error(request, f"❌ Erreur: {e}")
    
    return redirect('gestion_securite')

@role_required('admin')
def verifier_synchronisation_groupes(request):
    """Vérifie l'état de synchronisation des groupes Django"""
    if request.method == 'GET':
        try:
            utilisateurs = Utilisateur.objects.filter(role_autorise__isnull=False)
            desynchronises = []
            
            for utilisateur in utilisateurs:
                role = utilisateur.role_autorise
                group_mapping = {
                    'admin': 'administrateurs',
                    'medecin': 'medecins',
                    'patient': 'patients'
                }
                group_name = group_mapping.get(role, role)
                
                try:
                    group = Group.objects.get(name=group_name)
                    if not utilisateur.groups.filter(id=group.id).exists():
                        desynchronises.append({
                            'utilisateur': utilisateur.email,
                            'role': role,
                            'group_manquant': group_name
                        })
                except Group.DoesNotExist:
                    desynchronises.append({
                        'utilisateur': utilisateur.email,
                        'role': role,
                        'group_manquant': f"{group_name} (groupe n'existe pas)"
                    })
            
            if desynchronises:
                message = "❌ Utilisateurs désynchronisés:\n"
                for item in desynchronises[:5]:  # Limiter l'affichage
                    message += f"• {item['utilisateur']} -> {item['group_manquant']}\n"
                if len(desynchronises) > 5:
                    message += f"... et {len(desynchronises) - 5} autres"
                messages.warning(request, message)
            else:
                messages.success(request, "✅ Tous les groupes Django sont synchronisés")
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification: {e}")
            messages.error(request, f"❌ Erreur: {e}")
    
    return redirect('gestion_securite')


# Vues de test pour la sécurité
@login_required
@detecter_usurpation_role
@verifier_elevation_privileges
def test_acces_medecin(request):
    """Vue de test pour l'accès aux données médecin"""
    if request.user.role_autorise == 'medecin' or request.user.role_autorise == 'admin':
        # Log de l'accès autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.ACCES_MEDICAL,
            description="Accès autorisé aux données médecin",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.MOYEN
        )
        return HttpResponse("✅ Accès autorisé aux données médecin")
    else:
        # Log de la tentative d'accès non autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
            description="Tentative d'accès non autorisé aux données médecin",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.CRITIQUE
        )
        return HttpResponseForbidden("❌ Accès refusé : Vous n'avez pas les permissions pour accéder aux données médecin")

@login_required
@detecter_usurpation_role
@verifier_elevation_privileges
def test_acces_admin(request):
    """Vue de test pour l'accès aux données admin"""
    if request.user.role_autorise == 'admin':
        # Log de l'accès autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.ACCES_MEDICAL,
            description="Accès autorisé aux données admin",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.MOYEN
        )
        return HttpResponse("✅ Accès autorisé aux données admin")
    else:
        # Log de la tentative d'accès non autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
            description="Tentative d'accès non autorisé aux données admin",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.CRITIQUE
        )
        return HttpResponseForbidden("❌ Accès refusé : Vous n'avez pas les permissions pour accéder aux données admin")

@login_required
def test_acces_patient(request):
    """Vue de test pour l'accès aux données patient"""
    if request.user.role_autorise == 'patient' or request.user.role_autorise == 'medecin' or request.user.role_autorise == 'admin':
        # Log de l'accès autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.ACCES_PATIENT,
            description="Accès autorisé aux données patient",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.MOYEN
        )
        return HttpResponse("✅ Accès autorisé aux données patient")
    else:
        # Log de la tentative d'accès non autorisé
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
            description="Tentative d'accès non autorisé aux données patient",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.CRITIQUE
        )
        return HttpResponseForbidden("❌ Accès refusé : Vous n'avez pas les permissions pour accéder aux données patient")

def test_securite_page(request):
    """Page de test pour la sécurité"""
    return render(request, 'test_securite.html')

def simuler_usurpation_role(request, role_cible):
    """Simule une tentative d'usurpation de rôle"""
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Vous devez être connecté")
    
    role_actuel = request.user.role_autorise
    email_actuel = request.user.email
    
    # Log de la tentative d'usurpation
    AuditLog.log_action(
        utilisateur=request.user,
        type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
        description=f"Tentative d'usurpation: {role_actuel} → {role_cible}",
        request=request,
        niveau_risque=AuditLog.NiveauRisque.CRITIQUE
    )
    
    # Créer une alerte de sécurité
    AlerteSecurite.objects.create(
        type_alerte='TENTATIVE_ACCES_NON_AUTORISE',
        utilisateur_concerne=request.user,
        details=f"Tentative d'usurpation de rôle: {role_actuel} → {role_cible}",
        niveau_urgence='HAUTE',
        adresse_ip=request.META.get('REMOTE_ADDR', ''),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    # Simuler le changement de rôle dans la session (pour le test)
    request.session['role_simule'] = role_cible
    
    return HttpResponse(f"""
    <html>
    <head><title>Test d'Usurpation</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>🧪 Test d'Usurpation de Rôle</h2>
        <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px;">
            <h3>⚠️ Simulation d'Usurpation</h3>
            <p><strong>Utilisateur réel:</strong> {email_actuel} (Rôle: {role_actuel})</p>
            <p><strong>Rôle usurpé:</strong> {role_cible}</p>
            <p><strong>Date:</strong> {timezone.now()}</p>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>Tests à effectuer:</h3>
            <ul>
                <li><a href="/test/acces/medecin/">Tester accès médecin</a></li>
                <li><a href="/test/acces/admin/">Tester accès admin</a></li>
                <li><a href="/test/acces/patient/">Tester accès patient</a></li>
            </ul>
        </div>
        
        <div style="margin-top: 20px;">
            <a href="/test/securite/" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">
                ← Retour aux tests
            </a>
        </div>
    </body>
    </html>
    """)

def simuler_elevation_privileges(request):
    """Simule une tentative d'élévation de privilèges"""
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Vous devez être connecté")
    
    role_actuel = request.user.role_autorise
    
    # Déterminer le rôle cible selon le rôle actuel
    if role_actuel == 'patient':
        role_cible = 'medecin'
    elif role_actuel == 'medecin':
        role_cible = 'admin'
    else:
        role_cible = 'admin'  # Pour les admins, on simule une élévation vers super-admin
    
    return simuler_usurpation_role(request, role_cible)

def simuler_acces_direct_url(request, url_cible):
    """Simule un accès direct à une URL protégée"""
    if not request.user.is_authenticated:
        return HttpResponseForbidden("Vous devez être connecté")
    
    role_actuel = request.user.role_autorise
    
    # Log de la tentative d'accès direct
    AuditLog.log_action(
        utilisateur=request.user,
        type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
        description=f"Tentative d'accès direct à: {url_cible}",
        request=request,
        niveau_risque=AuditLog.NiveauRisque.ELEVE
    )
    
    return HttpResponse(f"""
    <html>
    <head><title>Test d'Accès Direct</title></head>
    <body style="font-family: Arial, sans-serif; padding: 20px;">
        <h2>🔓 Test d'Accès Direct</h2>
        <div style="background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px;">
            <h3>🚨 Tentative d'Accès Non Autorisé</h3>
            <p><strong>Utilisateur:</strong> {request.user.email} (Rôle: {role_actuel})</p>
            <p><strong>URL cible:</strong> {url_cible}</p>
            <p><strong>Date:</strong> {timezone.now()}</p>
        </div>
        
        <div style="margin-top: 20px;">
            <h3>Actions possibles:</h3>
            <ul>
                <li><a href="/test/acces/medecin/">Tester accès médecin</a></li>
                <li><a href="/test/acces/admin/">Tester accès admin</a></li>
                <li><a href="/test/securite/">Retour aux tests</a></li>
            </ul>
        </div>
    </body>
    </html>
    """)

def generate_unique_rfid_uid():
    """Génère un UID RFID unique au format hexadécimal (8 caractères)"""
    while True:
        # Générer un UID de 4 bytes en hexadécimal (8 caractères)
        uid = ''.join(random.choices(string.hexdigits.upper(), k=8))
        # Vérifier que cet UID n'existe pas déjà
        if not RFIDCard.objects.filter(card_uid=uid).exists():
            return uid

@role_required('admin')
def create_user_view(request):
    """Vue pour la création d'utilisateurs par l'administrateur"""
    if request.method == 'POST':
        form = AdminCreateUserForm(request.POST)
        if form.is_valid():
            try:
                # Créer l'utilisateur
                user = form.save(commit=False)
                user.role_autorise = form.cleaned_data['role_autorise']
                
                # Désactiver temporairement la synchronisation automatique
                post_save.disconnect(auto_sync_user_to_keycloak, sender='comptes.Utilisateur')
                
                try:
                    user.save()
                finally:
                    # Réactiver la synchronisation automatique
                    post_save.connect(auto_sync_user_to_keycloak, sender='comptes.Utilisateur')
                
                # Assigner le groupe correspondant
                from django.contrib.auth.models import Group
                group = Group.objects.get(name=form.cleaned_data['role_autorise'])
                user.groups.add(group)
                
                # Créer le profil spécifique selon le rôle
                role_autorise = form.cleaned_data['role_autorise']
                
                if role_autorise == 'medecin':
                    medecin = MedecinNew.objects.create(
                        utilisateur=user,
                        numero_ordre=form.cleaned_data.get('numero_praticien', 'NON_RENSEIGNE'),
                    )
                    # Ajouter la spécialité si fournie
                    specialite_nom = form.cleaned_data.get('specialite')
                    if specialite_nom:
                        try:
                            from comptes.models import SpecialiteMedicale
                            specialite, created = SpecialiteMedicale.objects.get_or_create(
                                nom=specialite_nom.strip(),
                                defaults={'description': f'Spécialité: {specialite_nom}'}
                            )
                            medecin.specialites.add(specialite)
                        except Exception as e:
                            logger.error(f"Erreur lors de l'ajout de la spécialité: {e}")
                    
                    # Créer la carte RFID si l'UID a été fourni lors du scan
                    if form.cleaned_data.get('rfid_uid'):
                        RFIDCard.objects.create(
                            utilisateur=user,
                            card_uid=form.cleaned_data.get('rfid_uid'),
                            actif=True,
                            access_direct=True  # Accès direct sans OTP pour les cartes créées par admin
                        )
                        logger.info(f"Carte RFID {form.cleaned_data.get('rfid_uid')} créée pour le médecin {user.email} avec accès direct")
                    
                    if form.cleaned_data.get('badge_bleu_uid'):
                        # Gérer les badges séparément
                        pass
                    
                elif role_autorise == 'patient':
                    patient = PatientNew.objects.create(
                        utilisateur=user,
                        date_naissance=form.cleaned_data['date_naissance'],
                        numero_securite_sociale=form.cleaned_data.get('numero_dossier', '')  # Mapper numero_dossier vers numero_securite_sociale
                    )
                    # Créer la carte RFID si l'UID a été fourni lors du scan par l'admin
                    if form.cleaned_data.get('rfid_uid'):
                        RFIDCard.objects.create(
                            utilisateur=user,
                            card_uid=form.cleaned_data.get('rfid_uid'),
                            actif=True,
                            access_direct=True  # Accès direct sans OTP pour les cartes créées par admin
                        )
                        logger.info(f"Carte RFID {form.cleaned_data.get('rfid_uid')} créée pour le patient {user.email} avec accès direct")
                    
                    if form.cleaned_data.get('badge_bleu_uid'):
                        # Gérer les badges séparément
                        pass
                    patient.save()
                    
                elif role_autorise == 'admin':
                    # Les admins sont gérés par les groupes Django
                    # Le niveau d'accès peut être stocké dans le profil utilisateur si nécessaire
                    pass
                
                # Créer l'utilisateur dans Keycloak avec le rôle
                try:
                    logger.info(f"Tentative de création de l'utilisateur {user.email} dans Keycloak avec le rôle {role_autorise}")
                    keycloak_success = create_keycloak_user_with_role(user, role_autorise, form.cleaned_data['password1'])
                    
                    # Préparer l'email HTML personnalisé
                    role_labels = {
                        'admin': 'Administrateur',
                        'medecin': 'Médecin',
                        'patient': 'Patient',
                    }
                    role_label = role_labels.get(role_autorise, role_autorise)
                    
                    subject = "Bienvenue sur KeurDoctor – Création de votre compte"
                    html_message = render_to_string("emails/creation_compte.html", {
                        "prenom": user.prenom,
                        "nom": user.nom,
                        "role": role_label,
                        "email": user.email,
                        "password": form.cleaned_data['password1'],
                        "lien_connexion": "http://localhost:8080/realms/KeurDoctorSecure/protocol/openid-connect/auth?client_id=django-KDclient&redirect_uri=http://localhost:8000&response_type=code"
                    })
                    plain_message = strip_tags(html_message)
                    from_email = "bobcodeur@gmail.com"
                    to = user.email
                    
                    # Envoyer l'email
                    try:
                        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
                        logger.info(f"Email de bienvenue envoyé à {user.email}")
                    except Exception as email_error:
                        logger.error(f"Erreur lors de l'envoi de l'email: {email_error}")
                    
                    if keycloak_success:
                        # Ajouter les attributs RFID dans Keycloak si fournis
                        if form.cleaned_data.get('rfid_uid') or form.cleaned_data.get('badge_bleu_uid'):
                            rfid_success = update_keycloak_rfid_attributes(user, form.cleaned_data.get('rfid_uid'), form.cleaned_data.get('badge_bleu_uid'))
                            if rfid_success:
                                logger.info(f"Attributs RFID mis à jour pour {user.email} dans Keycloak")
                            else:
                                logger.warning(f"Échec de la mise à jour des attributs RFID pour {user.email}")
                        
                        messages.success(request, f"✅ Utilisateur {user.email} créé avec succès dans Django et Keycloak avec le rôle {role_label}.")
                        logger.info(f"Utilisateur {user.email} créé avec succès dans Django et Keycloak")
                    else:
                        messages.warning(request, f"⚠️ Utilisateur {user.email} créé dans Django mais erreur lors de la création dans Keycloak. L'email de confirmation a été envoyé. Vous pouvez synchroniser manuellement plus tard.")
                        logger.error(f"Échec de la création Keycloak pour {user.email}")
                except Exception as e:
                    logger.error(f"Erreur lors de la création Keycloak: {e}")
                    
                    # Envoyer l'email même en cas d'exception
                    role_labels = {
                        'admin': 'Administrateur',
                        'medecin': 'Médecin',
                        'patient': 'Patient',
                    }
                    role_label = role_labels.get(role_autorise, role_autorise)
                    
                    subject = "Bienvenue sur KeurDoctor – Création de votre compte"
                    html_message = render_to_string("emails/creation_compte.html", {
                        "prenom": user.prenom,
                        "nom": user.nom,
                        "role": role_label,
                        "email": user.email,
                        "password": form.cleaned_data['password1'],
                        "lien_connexion": "http://localhost:8080/realms/KeurDoctorSecure/protocol/openid-connect/auth?client_id=django-KDclient&redirect_uri=http://localhost:8000&response_type=code"
                    })
                    plain_message = strip_tags(html_message)
                    from_email = "bobcodeur@gmail.com"
                    to = user.email
                    
                    try:
                        send_mail(subject, plain_message, from_email, [to], html_message=html_message)
                        logger.info(f"Email de bienvenue envoyé à {user.email} malgré l'erreur Keycloak")
                    except Exception as email_error:
                        logger.error(f"Erreur lors de l'envoi de l'email: {email_error}")
                    
                    messages.warning(request, f"⚠️ Utilisateur {user.email} créé dans Django mais erreur lors de la création dans Keycloak. L'email de confirmation a été envoyé. Vous pouvez synchroniser manuellement plus tard.")
                
                # Créer une alerte de sécurité
                AlerteSecurite.objects.create(
                    type_alerte='CREATION_UTILISATEUR',
                    utilisateur_concerne=user,
                    details=f"Utilisateur créé par l'administrateur {request.user.email} avec le rôle {role_autorise}",
                    niveau_urgence='BASSE',
                    admin_qui_a_bloque=request.user
                )
                
                return redirect('user_management')
                
            except Exception as e:
                logger.error(f"Erreur lors de la création d'utilisateur: {e}")
                messages.error(request, f"Erreur lors de la création de l'utilisateur: {e}")
    else:
        form = AdminCreateUserForm()
    
    return render(request, 'admin/create_user.html', {
        'form': form,
        'title': 'Créer un nouvel utilisateur'
    })

def update_keycloak_rfid_attributes(utilisateur, rfid_uid, badge_bleu_uid):
    """Met à jour les attributs RFID dans Keycloak"""
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            logger.error("Impossible d'obtenir le token admin Keycloak")
            return False

        # Récupérer l'ID de l'utilisateur dans Keycloak
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={utilisateur.email}"
        search_resp = requests.get(search_url, headers=headers)
        
        if search_resp.status_code != 200 or not search_resp.json():
            logger.error("Utilisateur introuvable dans Keycloak")
            return False
            
        user_id = search_resp.json()[0]['id']
        
        # Préparer les attributs RFID
        attributes = {}
        if rfid_uid:
            attributes['rfid_uid'] = [rfid_uid]
        if badge_bleu_uid:
            attributes['badge_bleu_uid'] = [badge_bleu_uid]
        
        # Mettre à jour les attributs
        update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        update_data = {"attributes": attributes}
        
        response = requests.put(update_url, json=update_data, headers=headers)
        
        if response.status_code in (204, 200):
            logger.info(f"Attributs RFID mis à jour pour {utilisateur.email} dans Keycloak")
            return True
        else:
            logger.error(f"Erreur lors de la mise à jour des attributs RFID: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des attributs RFID: {e}")
        return False


@csrf_exempt
@require_http_methods(["POST"])
def api_rfid_auth(request):
    """
    API pour valider une authentification RFID (utilisée par le Raspberry Pi ou le polling web).
    Reçoit : email, card_uid
    Vérifie que la carte est bien liée à l'utilisateur (admin ou patient, actif).
    Sécurise le polling : seul l'utilisateur de la session peut valider sa carte.
    Nettoie la session après succès.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        card_uid = data.get('card_uid')
        # Sécurité : vérifier que l'email correspond à la session
        session_email = request.session.get('rfid_auth_email')
        if not session_email or email != session_email:
            return JsonResponse({'success': False, 'message': 'Session non valide ou email non autorisé.'}, status=403)
        if not email:
            return JsonResponse({'success': False, 'message': 'Paramètres manquants.'}, status=400)
        try:
            utilisateur = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé.'}, status=404)
        if utilisateur.role_autorise not in ['admin', 'patient']:
            return JsonResponse({'success': False, 'message': 'Rôle non autorisé pour RFID.'}, status=403)
        # Si card_uid est null (polling), ne rien valider, juste attendre
        if not card_uid:
            return JsonResponse({'success': False, 'message': 'En attente de la lecture de la carte.'}, status=200)
        try:
            rfid_card = RFIDCard.objects.get(utilisateur=utilisateur, card_uid=card_uid, actif=True)
        except RFIDCard.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Carte RFID non reconnue ou non active.'}, status=401)
        # Authentification RFID réussie : nettoyer la session
        if 'rfid_auth_email' in request.session:
            del request.session['rfid_auth_email']
        return JsonResponse({'success': True, 'message': 'Authentification RFID réussie.'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Erreur technique : {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_rfid_patient_auth(request):
    """
    API spécifique pour l'authentification RFID des patients avec validation OTP.
    Reçoit : email, card_uid, otp_code
    Vérifie que la carte est liée à un patient et valide le code OTP.
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        card_uid = data.get('card_uid')
        otp_code = data.get('otp_code')
        
        if not email or not card_uid:
            return JsonResponse({'success': False, 'message': 'Paramètres manquants.'}, status=400)
        
        try:
            utilisateur = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Utilisateur non trouvé.'}, status=404)
        
        # Vérifier que c'est bien un patient
        if utilisateur.role_autorise != 'patient':
            return JsonResponse({'success': False, 'message': 'Seuls les patients peuvent utiliser cette méthode d\'authentification.'}, status=403)
        
        # Vérifier que l'utilisateur n'est pas bloqué
        if utilisateur.est_bloque:
            return JsonResponse({'success': False, 'message': 'Votre compte est bloqué. Contactez l\'administrateur.'}, status=403)
        
        # Vérifier la carte RFID
        try:
            rfid_card = RFIDCard.objects.get(utilisateur=utilisateur, card_uid=card_uid, actif=True)
        except RFIDCard.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Carte RFID non reconnue ou non active.'}, status=401)
        
        # Si pas de code OTP fourni, retourner succès pour la première étape
        if not otp_code:
            # Stocker l'email en session pour la validation OTP
            request.session['rfid_patient_email'] = email
            request.session['rfid_card_uid'] = card_uid
            return JsonResponse({
                'success': True, 
                'message': 'Carte RFID reconnue. Veuillez entrer votre code OTP.',
                'requires_otp': True
            })
        
        # Valider le code OTP (simulation - en production, utiliser un vrai système OTP)
        if otp_code == '123456':  # Code OTP de test
            # Authentification réussie
            # Nettoyer la session
            if 'rfid_patient_email' in request.session:
                del request.session['rfid_patient_email']
            if 'rfid_card_uid' in request.session:
                del request.session['rfid_card_uid']
            
            # Enregistrer l'authentification réussie
            HistoriqueAuthentification.objects.create(
                utilisateur=utilisateur,
                type_auth='NFC_CARTE',
                succes=True,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                role_tente='patient',
                role_autorise='patient'
            )
            
            return JsonResponse({
                'success': True, 
                'message': 'Authentification RFID + OTP réussie.',
                'redirect_url': '/patient/'
            })
        else:
            # Code OTP incorrect
            return JsonResponse({'success': False, 'message': 'Code OTP incorrect.'}, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Données JSON invalides.'}, status=400)
    except Exception as e:
        logger.error(f"Erreur lors de l'authentification RFID patient: {e}")
        return JsonResponse({'success': False, 'message': f'Erreur technique : {str(e)}'}, status=500)


def patient_rfid_login(request):
    """
    Page de connexion RFID pour les patients.
    Permet aux patients de se connecter avec leur carte RFID + OTP.
    """
    if request.method == 'POST':
        # Traitement du formulaire de connexion RFID
        email = request.POST.get('email')
        card_uid = request.POST.get('card_uid')
        
        if email and card_uid:
            try:
                utilisateur = Utilisateur.objects.get(email=email)
                
                # Vérifier que c'est bien un patient
                if utilisateur.role_autorise != 'patient':
                    messages.error(request, "Seuls les patients peuvent utiliser cette méthode d'authentification.")
                    return redirect('patient_rfid_login')
                
                # Vérifier que l'utilisateur n'est pas bloqué
                if utilisateur.est_bloque:
                    messages.error(request, f"Votre compte est bloqué: {utilisateur.raison_blocage}")
                    return redirect('patient_rfid_login')
                
                # Vérifier la carte RFID
                try:
                    rfid_card = RFIDCard.objects.get(utilisateur=utilisateur, card_uid=card_uid, actif=True)
                except RFIDCard.DoesNotExist:
                    messages.error(request, "Carte RFID non reconnue ou non active.")
                    return redirect('patient_rfid_login')
                
                # Stocker les informations en session pour la validation OTP
                request.session['rfid_patient_email'] = email
                request.session['rfid_card_uid'] = card_uid
                
                return redirect('patient_rfid_otp')
                
            except Utilisateur.DoesNotExist:
                messages.error(request, "Utilisateur non trouvé.")
                return redirect('patient_rfid_login')
    
    return render(request, 'rfid/patient_rfid_login.html')


def patient_rfid_otp(request):
    """
    Page de validation OTP après lecture RFID pour les patients.
    """
    # Vérifier que l'utilisateur a bien passé par l'étape RFID
    email = request.session.get('rfid_patient_email')
    card_uid = request.session.get('rfid_card_uid')
    
    if not email or not card_uid:
        messages.error(request, "Session invalide. Veuillez recommencer l'authentification RFID.")
        return redirect('patient_rfid_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        
        if otp_code:
            # Valider le code OTP (simulation - en production, utiliser un vrai système OTP)
            if otp_code == '123456':  # Code OTP de test
                try:
                    utilisateur = Utilisateur.objects.get(email=email)
                    
                    # Nettoyer la session
                    del request.session['rfid_patient_email']
                    del request.session['rfid_card_uid']
                    
                    # Enregistrer l'authentification réussie
                    HistoriqueAuthentification.objects.create(
                        utilisateur=utilisateur,
                        type_auth='NFC_CARTE',
                        succes=True,
                        adresse_ip=request.META.get('REMOTE_ADDR', ''),
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        role_tente='patient',
                        role_autorise='patient'
                    )
                    
                    # Rediriger vers le dashboard patient
                    messages.success(request, "Authentification RFID + OTP réussie !")
                    return redirect('patient_dashboard')
                    
                except Utilisateur.DoesNotExist:
                    messages.error(request, "Erreur lors de l'authentification.")
                    return redirect('patient_rfid_login')
            else:
                messages.error(request, "Code OTP incorrect. Veuillez réessayer.")
    
    return render(request, 'rfid/patient_rfid_otp.html', {
        'email': email,
        'card_uid': card_uid
    })


def methodes_authentification(request):
    """
    Page d'information sur les différentes méthodes d'authentification disponibles.
    """
    return render(request, 'authentification/methodes.html')


@login_required
def enregistrer_rfid_view(request):
    """Vue pour qu'un utilisateur admin/patient enregistre sa propre carte RFID."""
    if request.user.role_autorise not in ['admin', 'patient']:
        messages.error(request, "Seuls les admins et patients peuvent enregistrer une carte RFID.")
        return redirect('home')
    if request.method == 'POST':
        form = RFIDCardRegisterForm(request.POST, user=request.user)
        if form.is_valid():
            card_uid = form.cleaned_data['card_uid']
            if RFIDCard.objects.filter(card_uid=card_uid).exists():
                messages.error(request, "Cette carte RFID est déjà enregistrée.")
            else:
                RFIDCard.objects.create(utilisateur=request.user, card_uid=card_uid)
                messages.success(request, "Carte RFID enregistrée avec succès.")
                return redirect('enregistrer_rfid')
    else:
        form = RFIDCardRegisterForm(user=request.user)
    cartes = RFIDCard.objects.filter(utilisateur=request.user)
    return render(request, 'rfid/enregistrer_rfid.html', {'form': form, 'cartes': cartes, 'user_target': request.user})

@login_required
def enregistrer_rfid_admin_view(request, user_id):
    """Vue pour qu'un admin enregistre une carte RFID pour n'importe quel utilisateur."""
    if request.user.role_autorise != 'admin':
        messages.error(request, "Accès réservé aux administrateurs.")
        return redirect('home')
    user_target = get_object_or_404(Utilisateur, id=user_id, role_autorise__in=['admin', 'patient'])
    if request.method == 'POST':
        form = RFIDCardRegisterForm(request.POST, user=request.user)
        if form.is_valid():
            card_uid = form.cleaned_data['card_uid']
            if RFIDCard.objects.filter(card_uid=card_uid).exists():
                messages.error(request, "Cette carte RFID est déjà enregistrée.")
            else:
                RFIDCard.objects.create(utilisateur=user_target, card_uid=card_uid)
                messages.success(request, f"Carte RFID enregistrée pour {user_target.email}.")
                return redirect('enregistrer_rfid_admin', user_id=user_target.id)
    else:
        form = RFIDCardRegisterForm(user=request.user, initial={'utilisateur': user_target})
    cartes = RFIDCard.objects.filter(utilisateur=user_target)
    return render(request, 'rfid/enregistrer_rfid.html', {'form': form, 'cartes': cartes, 'user_target': user_target})

@login_required
def rfid_wait_view(request):
    """Page d'attente RFID après OTP. Stocke l'email en session et affiche la page d'attente."""
    if request.user.role_autorise not in ['admin', 'patient']:
        messages.error(request, "Seuls les admins et patients peuvent utiliser la double authentification RFID.")
        return redirect('home')
    # Stocker l'email en session pour le polling
    request.session['rfid_auth_email'] = request.user.email
    return render(request, 'rfid/wait_rfid.html', {'user_email': request.user.email})


@login_required
@staff_member_required
def admin_stats(request):
    from comptes.models import Utilisateur, Medecin, Patient, RendezVous
    from django.db.models import Count, Q
    from django.utils import timezone
    from datetime import timedelta, datetime
    from django.http import JsonResponse
    import json
    
    # Récupération des stats de base
    users_count = Utilisateur.objects.count()
    medecins_count = MedecinNew.objects.count()
    patients_count = PatientNew.objects.count()
    rdv_count = RendezVous.objects.count()
    
    # Activité récente
    recent_users = Utilisateur.objects.order_by('-date_creation')[:10]
    recent_rdv = RendezVous.objects.order_by('-date_rdv')[:10]
    
    # Données pour graphique évolution (12 derniers mois)
    today = timezone.now()
    months_data = []
    evolution_users = []
    evolution_rdv = []
    
    for i in range(12):
        month_start = today.replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)
        month_end = month_end - timedelta(days=month_end.day)
        
        users_month = Utilisateur.objects.filter(
            date_creation__gte=month_start,
            date_creation__lte=month_end
        ).count()
        
        rdv_month = RendezVous.objects.filter(
            date_rdv__gte=month_start,
            date_rdv__lte=month_end
        ).count()
        
        months_data.insert(0, month_start.strftime('%b'))
        evolution_users.insert(0, users_month)
        evolution_rdv.insert(0, rdv_month)
    
    # Données pour graphique répartition par rôle
    admin_count = Utilisateur.objects.filter(role_autorise='admin').count()
    medecin_count_role = Utilisateur.objects.filter(role_autorise='medecin').count()
    patient_count_role = Utilisateur.objects.filter(role_autorise='patient').count()
    
    # Si les comptes par rôle sont vides, utiliser les profils spécialisés
    if medecin_count_role == 0:
        medecin_count_role = medecins_count
    if patient_count_role == 0:
        patient_count_role = patients_count
    
    repartition_data = [medecin_count_role, patient_count_role, admin_count]
    repartition_labels = ['Médecins', 'Patients', 'Admins']
    
    # Top médecins par nombre de rendez-vous
    top_medecins = RendezVous.objects.values('medecin__utilisateur__nom', 'medecin__utilisateur__prenom') \
                    .annotate(rdv_count=Count('id')) \
                    .order_by('-rdv_count')[:5]
    
    top_medecins_labels = [f"Dr. {m['medecin__utilisateur__prenom']} {m['medecin__utilisateur__nom']}" for m in top_medecins]
    top_medecins_data = [m['rdv_count'] for m in top_medecins]
    
    # Si c'est une requête AJAX, retourner les données JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'users_count': users_count,
            'medecins_count': medecins_count,
            'patients_count': patients_count,
            'rdv_count': rdv_count,
            'evolution_users': evolution_users,
            'evolution_rdv': evolution_rdv,
            'repartition_data': repartition_data,
            'top_medecins_labels': top_medecins_labels,
            'top_medecins_data': top_medecins_data,
        })
    
    context = {
        'users_count': users_count,
        'medecins_count': medecins_count,
        'patients_count': patients_count,
        'rdv_count': rdv_count,
        'recent_users': recent_users,
        'recent_rdv': recent_rdv,
        # Données pour les graphiques
        'evolution_months': json.dumps(months_data),
        'evolution_users': json.dumps(evolution_users),
        'evolution_rdv': json.dumps(evolution_rdv),
        'repartition_labels': json.dumps(repartition_labels),
        'repartition_data': json.dumps(repartition_data),
        'top_medecins_labels': json.dumps(top_medecins_labels),
        'top_medecins_data': json.dumps(top_medecins_data),
    }
    
    return render(request, 'dashboards/admin_stats.html', context)


@login_required 
def https_status_view(request):
    """
    Vue pour afficher le statut de sécurité HTTPS en temps réel
    """
    # Informations sur la connexion actuelle
    connection_info = {
        'is_secure': request.is_secure(),
        'protocol': request.META.get('SERVER_PROTOCOL', 'HTTP/1.1'),
        'host': request.get_host(),
        'remote_addr': request.META.get('REMOTE_ADDR', 'Inconnu'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Inconnu'),
        'url_complete': request.build_absolute_uri(),
    }
    
    # Vérification des en-têtes de sécurité (simulation côté serveur)
    security_headers = {
        'hsts_enabled': True,  # Configuré dans settings
        'csp_enabled': True,   # Configuré dans middleware
        'x_frame_options': True,
        'x_content_type_options': True,
        'referrer_policy': True,
    }
    
    # Statistiques des connexions sécurisées (dernières 24h)
    from datetime import timedelta
    from django.utils import timezone
    
    date_limite = timezone.now() - timedelta(hours=24)
    
    # Logs des connexions HTTPS vs HTTP
    logs_stats = {
        'total_connections': 0,
        'https_connections': 0,
        'http_attempts': 0,
        'security_alerts': 0,
    }
    
    try:
        # Compter les alertes de sécurité liées aux tentatives HTTP
        logs_stats['security_alerts'] = AlerteSecurite.objects.filter(
            date_creation__gte=date_limite,
            type_alerte='TENTATIVE_ACCES_NON_AUTORISE'
        ).count()
        
        # Compter les connexions réussies
        logs_stats['total_connections'] = HistoriqueAuthentification.objects.filter(
            date_heure_acces__gte=date_limite,
            succes=True
        ).count()
        
    except Exception as e:
        logger.error(f"Erreur lors du calcul des statistiques HTTPS: {e}")
    
    # Informations sur les certificats SSL (simulation)
    ssl_info = {
        'certificate_valid': True,
        'certificate_issuer': 'KeurDoctor Self-Signed',
        'certificate_expiry': 'Dans 365 jours',
        'certificate_type': 'RSA 4096 bits',
    }
    
    # Recommandations de sécurité
    recommendations = []
    
    if not request.is_secure():
        recommendations.append({
            'level': 'danger',
            'message': 'Votre connexion n\'est pas sécurisée. Passez en HTTPS immédiatement.',
            'action': f'https://{request.get_host()}{request.get_full_path()}'
        })
    
    if 'localhost' in request.get_host() or '127.0.0.1' in request.get_host():
        recommendations.append({
            'level': 'warning',
            'message': 'Vous utilisez un certificat auto-signé. Pour la production, utilisez un certificat signé par une CA.',
            'action': None
        })
    
    if request.is_secure():
        recommendations.append({
            'level': 'success',
            'message': 'Excellent ! Votre connexion est parfaitement sécurisée en HTTPS.',
            'action': None
        })
    
    context = {
        'connection_info': connection_info,
        'security_headers': security_headers,
        'logs_stats': logs_stats,
        'ssl_info': ssl_info,
        'recommendations': recommendations,
        'title': 'Statut de Sécurité HTTPS'
    }
    
    # Logger l'accès à cette page de monitoring
    AuditLog.log_action(
        utilisateur=request.user,
        type_action=AuditLog.TypeAction.LECTURE_DONNEES,
        description="Consultation du statut de sécurité HTTPS",
        request=request,
        niveau_risque=AuditLog.NiveauRisque.FAIBLE
    )
    
    return render(request, 'securite/https_status.html', context)


