from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from django.contrib.auth.models import User, Group
import logging

logger = logging.getLogger(__name__)


class KeycloakOIDCAuthenticationBackend(OIDCAuthenticationBackend):
    """
    Backend d'authentification personnalisé pour Keycloak
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
    
    def assign_roles(self, user, claims):
        """Assigne les rôles Keycloak aux groupes Django"""
        # Récupération des rôles depuis les claims
        roles = []
        
        # Debug - Afficher tous les claims pour comprendre la structure
        logger.debug(f"Claims complets pour {user.username}: {claims}")
        
        # Rôles du realm
        if 'realm_access' in claims:
            realm_roles = claims['realm_access'].get('roles', [])
            roles.extend(realm_roles)
            logger.debug(f"Rôles realm trouvés: {realm_roles}")
        
        # Rôles du client spécifique
        if 'resource_access' in claims:
            client_id = 'django-KDclient'
            client_roles = claims['resource_access'].get(client_id, {}).get('roles', [])
            roles.extend(client_roles)
            logger.debug(f"Rôles client {client_id} trouvés: {client_roles}")
        
        # Rôles directement dans les claims (via mappers)
        if 'roles' in claims:
            direct_roles = claims['roles']
            if isinstance(direct_roles, list):
                roles.extend(direct_roles)
            elif isinstance(direct_roles, str):
                roles.append(direct_roles)
            logger.debug(f"Rôles directs trouvés: {direct_roles}")
        
        # Nettoyer et dédupliquer les rôles
        roles = list(set([role.lower() for role in roles if role]))
        logger.info(f"Rôles extraits pour {user.username}: {roles}")
        
        # Supprime tous les groupes existants
        user.groups.clear()
        
        # Mapping des rôles Keycloak vers les groupes Django
        role_mapping = {
            'admin': 'admin',
            'medecin': 'medecin', 
            'patient': 'patient',
        }
        
        roles_assigned = []
        permissions_set = False
        
        for role in roles:
            role_clean = role.lower().strip()
            if role_clean in role_mapping:
                group_name = role_mapping[role_clean]
                group, created = Group.objects.get_or_create(name=group_name)
                if created:
                    logger.info(f"Groupe Django '{group_name}' créé automatiquement")
                
                user.groups.add(group)
                roles_assigned.append(role_clean)
                
                # Permissions spéciales pour admin
                if role_clean == 'admin':
                    user.is_staff = True
                    user.is_superuser = True
                    permissions_set = True
        
        # Si aucun rôle admin, retirer les privilèges
        if not permissions_set:
            user.is_staff = False
            user.is_superuser = False
        
        user.save()
        logger.info(f"Rôles assignés à {user.username}: {roles_assigned}")
        logger.info(f"Groupes Django: {[group.name for group in user.groups.all()]}")
        logger.info(f"Staff: {user.is_staff}, Superuser: {user.is_superuser}")
    
    def get_userinfo(self, access_token, id_token, payload):
        """Récupère les informations utilisateur depuis Keycloak"""
        userinfo = super().get_userinfo(access_token, id_token, payload)
        
        # Ajouter des informations supplémentaires si nécessaire
        return userinfo
