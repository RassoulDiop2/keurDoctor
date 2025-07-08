from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.contrib.auth import logout
from django.contrib import messages
from urllib.parse import urlencode
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
import json
from .decorators import role_required, any_role_required
from .forms import InscriptionForm, AdminCreateUserForm
from .models import Utilisateur, Medecin, Patient, AlerteSecurite, HistoriqueAuthentification, Administrateur
import logging
import requests
import uuid
from django.conf import settings

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
    
    return render(request, 'dashboards/admin.html', {
        'user': request.user,
        'title': 'Administration',
        'alertes_non_lues': alertes_non_lues,
        'utilisateurs_bloques': utilisateurs_bloques,
        'alertes_critiques': alertes_critiques,
        'utilisateurs_en_attente': utilisateurs_en_attente,
        'alertes_non_lues_count': alertes_non_lues_count,
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

        logger.info(f"Synchronisation Keycloak réussie pour {utilisateur.email} - Rôle: {role}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation Keycloak: {e}")
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
    """Dashboard médecin"""
    return render(request, 'dashboards/medecin.html', {
        'user': request.user,
        'title': 'Espace Médecin'
    })


@role_required('patient')
def patient_dashboard(request):
    """Dashboard patient"""
    return render(request, 'dashboards/patient.html', {
        'user': request.user,
        'title': 'Espace Patient'
    })


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
                
                # Créer une alerte pour l'admin
                AlerteSecurite.objects.create(
                    type_alerte='NOUVEL_UTILISATEUR_EN_ATTENTE',
                    utilisateur_concerne=utilisateur,
                    details=f"Nouvel utilisateur inscrit : {utilisateur.email}. Rôle à attribuer.",
                    niveau_urgence='MOYENNE'
                )
                
                # Créer l'utilisateur dans Keycloak
                if create_keycloak_user(utilisateur, role):
                    # Créer le profil spécifique selon le rôle (optionnel, car pas encore autorisé)
                    if role == 'medecin':
                        Medecin.objects.create(
                            utilisateur=utilisateur,
                            specialite=form.cleaned_data['specialite'],
                            numero_praticien=form.cleaned_data['numero_praticien']
                        )
                    elif role == 'patient':
                        Patient.objects.create(
                            utilisateur=utilisateur,
                            date_naissance=form.cleaned_data['date_naissance'],
                            numero_dossier=form.cleaned_data['numero_dossier']
                        )
                    
                    messages.success(request, f'Inscription réussie ! Votre compte a été créé et est en attente de validation par un administrateur.')
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

def create_keycloak_user(utilisateur, role):
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            logger.error("Impossible d'obtenir le token admin Keycloak")
            return False

        # Création de l'utilisateur
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
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        response = requests.post(url, json=user_data, headers=headers, timeout=10)
        if response.status_code != 201:
            logger.error(f"Erreur création Keycloak: {response.status_code} - {response.text}")
            return False

        # Récupérer l'ID de l'utilisateur créé
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={utilisateur.email}"
        search_resp = requests.get(search_url, headers=headers)
        if search_resp.status_code != 200 or not search_resp.json():
            logger.error("Utilisateur créé mais impossible de le retrouver pour l'affectation du mot de passe/groupe.")
            return False
        user_id = search_resp.json()[0]['id']

        # Définir un mot de passe temporaire (exemple : "ChangeMe123!")
        password_payload = {
            "type": "password",
            "value": "ChangeMe123!",
            "temporary": True  # L'utilisateur devra le changer à la première connexion
        }
        pwd_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/reset-password"
        pwd_resp = requests.put(pwd_url, json=password_payload, headers=headers)
        if pwd_resp.status_code not in (204, 200):
            logger.error(f"Erreur lors de l'affectation du mot de passe: {pwd_resp.status_code} - {pwd_resp.text}")

        # Ajouter l'utilisateur au groupe
        group_name = "medecins" if role == "medecin" else "patients"
        # Chercher l'ID du groupe
        group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
        group_resp = requests.get(group_url, headers=headers)
        if group_resp.status_code == 200:
            groups = group_resp.json()
            group_id = next((g['id'] for g in groups if g['name'] == group_name), None)
            if group_id:
                add_group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups/{group_id}"
                add_group_resp = requests.put(add_group_url, headers=headers)
                if add_group_resp.status_code not in (204, 200):
                    logger.error(f"Erreur lors de l'ajout au groupe: {add_group_resp.status_code} - {add_group_resp.text}")
            else:
                logger.error(f"Groupe {group_name} introuvable dans Keycloak.")
        else:
            logger.error("Impossible de récupérer la liste des groupes Keycloak.")

        return True

    except Exception as e:
        logger.error(f"Erreur lors de la création Keycloak: {e}")
        return False

@role_required('admin')
def synchroniser_utilisateur_keycloak(request, user_id):
    """Synchronise manuellement un utilisateur avec Keycloak"""
    if request.method == 'POST':
        try:
            utilisateur = get_object_or_404(Utilisateur, id=user_id)
            
            # Synchroniser le rôle actuel
            if utilisateur.role_autorise:
                sync_success = sync_role_to_keycloak(utilisateur, utilisateur.role_autorise)
                
                if sync_success:
                    messages.success(request, f"Utilisateur {utilisateur.email} synchronisé avec Keycloak (rôle: {utilisateur.role_autorise})")
                else:
                    messages.error(request, f"Erreur lors de la synchronisation de {utilisateur.email} avec Keycloak")
            else:
                messages.warning(request, f"Utilisateur {utilisateur.email} n'a pas de rôle autorisé à synchroniser")
                
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation: {e}")
            messages.error(request, f"Erreur lors de la synchronisation: {e}")
    
    return redirect('gestion_securite')

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
                user.save()
                
                # Assigner le groupe correspondant
                from django.contrib.auth.models import Group
                group = Group.objects.get(name=form.cleaned_data['role_autorise'])
                user.groups.add(group)
                
                # Créer le profil spécifique selon le rôle
                role_autorise = form.cleaned_data['role_autorise']
                
                if role_autorise == 'medecin':
                    Medecin.objects.create(
                        utilisateur=user,
                        specialite=form.cleaned_data['specialite'],
                        numero_praticien=form.cleaned_data['numero_praticien']
                    )
                elif role_autorise == 'patient':
                    Patient.objects.create(
                        utilisateur=user,
                        date_naissance=form.cleaned_data['date_naissance'],
                        numero_dossier=form.cleaned_data['numero_dossier']
                    )
                elif role_autorise == 'admin':
                    Administrateur.objects.create(
                        utilisateur=user,
                        niveau_acces=form.cleaned_data['niveau_acces']
                    )
                
                # Créer l'utilisateur dans Keycloak avec le rôle
                try:
                    keycloak_success = create_keycloak_user_with_role(user, role_autorise, form.cleaned_data['password1'])
                    if keycloak_success:
                        messages.success(request, f"Utilisateur {user.email} créé avec succès dans Django et Keycloak.")
                    else:
                        messages.warning(request, f"Utilisateur {user.email} créé dans Django mais erreur lors de la création dans Keycloak.")
                except Exception as e:
                    logger.error(f"Erreur lors de la création Keycloak: {e}")
                    messages.warning(request, f"Utilisateur {user.email} créé dans Django mais erreur lors de la création dans Keycloak.")
                
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


def create_keycloak_user_with_role(utilisateur, role, password):
    """Crée un utilisateur dans Keycloak avec le rôle spécifié"""
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            logger.error("Impossible d'obtenir le token admin Keycloak")
            return False

        # Création de l'utilisateur
        user_data = {
            "username": utilisateur.email,
            "email": utilisateur.email,
            "firstName": utilisateur.prenom,
            "lastName": utilisateur.nom,
            "enabled": True,
            "emailVerified": True,
            "credentials": [
                {
                    "type": "password",
                    "value": password,
                    "temporary": False
                }
            ],
            "attributes": {
                "keycloak_id": [str(utilisateur.keycloak_id)],
                "role": [role]
            }
        }
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Créer l'utilisateur
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        response = requests.post(url, json=user_data, headers=headers, timeout=10)
        
        if response.status_code != 201:
            logger.error(f"Erreur création Keycloak: {response.status_code} - {response.text}")
            return False

        # Récupérer l'ID de l'utilisateur créé
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={utilisateur.email}"
        search_resp = requests.get(search_url, headers=headers)
        
        if search_resp.status_code != 200 or not search_resp.json():
            logger.error("Utilisateur créé mais impossible de le retrouver pour l'affectation du rôle.")
            return False
            
        user_id = search_resp.json()[0]['id']

        # Attribuer le rôle à l'utilisateur
        role_mapping_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
        
        # Récupérer l'ID du rôle
        roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/roles"
        roles_resp = requests.get(roles_url, headers=headers)
        
        if roles_resp.status_code == 200:
            roles = roles_resp.json()
            role_id = next((r['id'] for r in roles if r['name'] == role), None)
            
            if role_id:
                role_payload = [{"id": role_id, "name": role}]
                role_resp = requests.post(role_mapping_url, json=role_payload, headers=headers)
                
                if role_resp.status_code not in (204, 200):
                    logger.error(f"Erreur lors de l'attribution du rôle: {role_resp.status_code} - {role_resp.text}")
                    return False
                else:
                    logger.info(f"Rôle {role} attribué avec succès à l'utilisateur {utilisateur.email}")
            else:
                logger.error(f"Rôle {role} introuvable dans Keycloak.")
                return False
        else:
            logger.error("Impossible de récupérer la liste des rôles Keycloak.")
            return False

        logger.info(f"Utilisateur {utilisateur.email} créé avec succès dans Keycloak avec le rôle {role}")
        return True

    except Exception as e:
        logger.error(f"Erreur lors de la création Keycloak: {e}")
        return False