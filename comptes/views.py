from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.generic import View
from django.contrib.auth import logout
from django.contrib import messages
from urllib.parse import urlencode
from .decorators import role_required, any_role_required
import logging
import requests
from django.conf import settings
from django.contrib.auth.models import User, Group
from .forms import InscriptionForm
from .keycloak_service import KeycloakService
from .models import UserProfile

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


@login_required
def redirection_role(request):
    """Redirige l'utilisateur vers son dashboard selon son rôle"""
    try:
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
        'is_superuser': request.user.is_superuser
    })
@role_required('admin')
def user_management(request):
    """Vue pour la gestion des utilisateurs"""
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin/user_management.html', {
        'users': users,
        'title': 'Gestion des utilisateurs'
    })

@role_required('admin')
def admin_dashboard(request):
    """Dashboard administrateur"""
    return render(request, 'dashboards/admin.html', {
        'user': request.user,
        'title': 'Administration'
    })


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
    if request.user.is_authenticated:
        messages.info(request, "Vous êtes déjà connecté.")
        return redirect('redirection_role')
    
    if request.method == 'POST':
        form = InscriptionForm(request.POST)
        if form.is_valid():
            try:
                # Récupérer les données du formulaire
                user_data = {
                    'username': form.cleaned_data['username'],
                    'email': form.cleaned_data['email'],
                    'first_name': form.cleaned_data['first_name'],
                    'last_name': form.cleaned_data['last_name'],
                    'password': form.cleaned_data['password1'],
                    'role': form.cleaned_data['role'],
                    'date_naissance': form.cleaned_data.get('date_naissance'),
                    'telephone': form.cleaned_data.get('telephone')
                }
                
                # Créer l'utilisateur dans Django
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password=user_data['password']
                )
                
                # Assigner le rôle dans Django
                try:
                    group = Group.objects.get(name=user_data['role'])
                    user.groups.add(group)
                except Group.DoesNotExist:
                    # Créer le groupe s'il n'existe pas
                    group = Group.objects.create(name=user_data['role'])
                    user.groups.add(group)
                
                # Mettre à jour le profil utilisateur
                if user_data.get('date_naissance') or user_data.get('telephone'):
                    profile = user.profile
                    if user_data.get('date_naissance'):
                        profile.date_naissance = user_data['date_naissance']
                    if user_data.get('telephone'):
                        profile.telephone = user_data['telephone']
                    profile.save()
                
                # Créer l'utilisateur dans Keycloak
                keycloak_service = KeycloakService()
                success, message = keycloak_service.create_user_in_keycloak(user_data)
                
                if success:
                    messages.success(request, f"Compte créé avec succès ! Vous pouvez maintenant vous connecter.")
                    logger.info(f"Nouvel utilisateur créé: {user.username} avec le rôle {user_data['role']}")
                    return redirect('home')
                else:
                    # Si Keycloak échoue, supprimer l'utilisateur Django
                    user.delete()
                    messages.error(request, f"Erreur lors de la création du compte: {message}")
                    logger.error(f"Échec création Keycloak pour {user_data['username']}: {message}")
                    
            except Exception as e:
                messages.error(request, f"Une erreur est survenue lors de l'inscription: {str(e)}")
                logger.error(f"Erreur lors de l'inscription: {e}")
        else:
            messages.error(request, "Veuillez corriger les erreurs dans le formulaire.")
    else:
        form = InscriptionForm()
    
    return render(request, 'inscription.html', {
        'form': form,
        'title': 'Inscription'
    })


def inscription_success_view(request):
    """Vue de succès après inscription"""
    return render(request, 'inscription_success.html', {
        'title': 'Inscription réussie'
    })