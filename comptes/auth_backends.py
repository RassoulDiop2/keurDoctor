from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User, Group
from django.http import HttpRequest
from django.utils import timezone
import logging
from .models import Utilisateur, AlerteSecurite, HistoriqueAuthentification

logger = logging.getLogger(__name__)


class KeycloakOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """
    Backend d'authentification personnalisé pour Keycloak avec contrôle de rôles
    """
    
    def create_user(self, claims):
        """Crée un nouvel utilisateur avec les informations de Keycloak"""
        email = claims.get('email')
        username = claims.get('preferred_username', email)
        first_name = claims.get('given_name', '')
        last_name = claims.get('family_name', '')
        
        user = self.UserModel.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        
        # Assigner les rôles
        self.assign_roles(user, claims)
        
        logger.info(f"Nouvel utilisateur créé: {username}")
        return user
    
    def update_user(self, user, claims):
        """Met à jour les informations utilisateur"""
        user.email = claims.get('email', user.email)
        user.first_name = claims.get('given_name', user.first_name)
        user.last_name = claims.get('family_name', user.last_name)
        user.save()
        
        # Mettre à jour les rôles
        self.assign_roles(user, claims)
        
        return user
    
    def authenticate(self, request, **kwargs):
        """Authentification avec contrôle de rôles"""
        # Récupérer le rôle tenté depuis la session ou les paramètres
        role_tente = None
        if hasattr(request, 'session'):
            role_tente = request.session.get('role_tente')
        if not role_tente and hasattr(request, 'GET'):
            role_tente = request.GET.get('role')
        
        # Authentification normale via OIDC
        user = super().authenticate(request, **kwargs)
        
        if user and role_tente:
            # Vérifier si l'utilisateur est bloqué
            if hasattr(user, 'est_bloque') and user.est_bloque:
                logger.warning(f"Tentative de connexion d'un utilisateur bloqué: {user.email}")
                self._enregistrer_tentative_incorrecte(user, role_tente, request, "Utilisateur bloqué")
                return None
            
            # Vérifier le rôle autorisé
            if not self._verifier_role_autorise(user, role_tente, request):
                return None
        
        return user
    
    def _verifier_role_autorise(self, user, role_tente, request):
        """Vérifie si l'utilisateur peut se connecter avec le rôle tenté"""
        # Récupérer le rôle autorisé de l'utilisateur
        role_autorise = getattr(user, 'role_autorise', None)
        
        if not role_autorise:
            # Si aucun rôle autorisé n'est défini, autoriser (compatibilité)
            logger.info(f"Aucun rôle autorisé défini pour {user.email}, autorisation accordée")
            return True
        
        # Vérifier si le rôle tenté correspond au rôle autorisé
        if role_tente.lower() == role_autorise.lower():
            logger.info(f"Connexion autorisée pour {user.email} avec le rôle {role_tente}")
            # Réinitialiser les tentatives incorrectes
            if hasattr(user, 'tentatives_connexion_incorrectes'):
                user.tentatives_connexion_incorrectes = 0
                user.save()
            return True
        else:
            # Rôle incorrect - bloquer l'utilisateur
            logger.warning(f"Tentative de connexion avec rôle incorrect: {user.email} - Tenté: {role_tente}, Autorisé: {role_autorise}")
            
            # Enregistrer la tentative incorrecte
            self._enregistrer_tentative_incorrecte(user, role_tente, request, f"Rôle incorrect: tenté {role_tente}, autorisé {role_autorise}")
            
            # Bloquer l'utilisateur
            user.bloquer(f"Tentative de connexion avec rôle incorrect: {role_tente} au lieu de {role_autorise}")
            
            # Créer une alerte admin
            AlerteSecurite.objects.create(
                type_alerte='TENTATIVE_ROLE_INCORRECT',
                utilisateur_concerne=user,
                details=f"Tentative de connexion avec rôle incorrect: {role_tente} au lieu de {role_autorise}",
                niveau_urgence='HAUTE',
                adresse_ip=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return False
    
    def _enregistrer_tentative_incorrecte(self, user, role_tente, request, raison):
        """Enregistre une tentative de connexion incorrecte"""
        # Incrémenter le compteur de tentatives
        if hasattr(user, 'incrementer_tentative_incorrecte'):
            user.incrementer_tentative_incorrecte()
        
        # Enregistrer dans l'historique
        HistoriqueAuthentification.objects.create(
            utilisateur=user,
            type_auth='TENTATIVE_ROLE_INCORRECT',
            succes=False,
            adresse_ip=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            role_tente=role_tente,
            role_autorise=getattr(user, 'role_autorise', 'Non défini')
        )
    
    def _get_client_ip(self, request):
        """Récupère l'adresse IP du client"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def assign_roles(self, user, claims):
        """Assigne les rôles Keycloak aux groupes Django et synchronise le champ role_autorise"""
        # Récupération des rôles depuis les claims
        roles = []
        logger.debug(f"Claims complets pour {user.username}: {claims}")
        if 'realm_access' in claims:
            realm_roles = claims['realm_access'].get('roles', [])
            roles.extend(realm_roles)
            logger.debug(f"Rôles realm trouvés: {realm_roles}")
        if 'resource_access' in claims:
            client_id = 'django-KDclient'
            client_roles = claims['resource_access'].get(client_id, {}).get('roles', [])
            roles.extend(client_roles)
            logger.debug(f"Rôles client {client_id} trouvés: {client_roles}")
        if 'roles' in claims:
            direct_roles = claims['roles']
            if isinstance(direct_roles, list):
                roles.extend(direct_roles)
            elif isinstance(direct_roles, str):
                roles.append(direct_roles)
            logger.debug(f"Rôles directs trouvés: {direct_roles}")
        roles = list(set([role.lower() for role in roles if role]))
        logger.info(f"Rôles extraits pour {user.username}: {roles}")
        user.groups.clear()
        role_mapping = {
            'admin': ('admin', 'administrateurs'),
            'medecin': ('medecin', 'medecins'),
            'patient': ('patient', 'patients'),
        }
        roles_assigned = []
        # Synchronisation du champ role_autorise : toujours mettre à jour selon le rôle principal trouvé
        main_role = None
        for role in ['admin', 'medecin', 'patient']:
            if role in roles:
                main_role = role
                break
        if main_role:
            group_name, group_django = role_mapping[main_role]
            group, _ = Group.objects.get_or_create(name=group_django)
            user.groups.add(group)
            user.role_autorise = group_name
            # Permissions spéciales pour admin
            if main_role == 'admin':
                user.is_staff = True
                user.is_superuser = True
            else:
                user.is_staff = False
                user.is_superuser = False
            user.save()
            logger.info(f"Champ role_autorise synchronisé: {user.email} -> {group_name}")
        else:
            user.role_autorise = None
            user.is_staff = False
            user.is_superuser = False
            user.save()
            logger.info(f"Aucun rôle principal trouvé pour {user.email}, role_autorise vidé.")
    
    def get_userinfo(self, access_token, id_token, payload):
        """Récupère les informations utilisateur depuis Keycloak"""
        userinfo = super().get_userinfo(access_token, id_token, payload)
        
        # Ajouter des informations supplémentaires si nécessaire
        return userinfo
