import requests
import json
import logging
from django.conf import settings
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)

class KeycloakService:
    """Service pour gérer les interactions avec Keycloak"""
    
    def __init__(self):
        self.base_url = settings.KEYCLOAK_SERVER_URL
        self.realm = settings.OIDC_REALM
        self.admin_username = settings.KEYCLOAK_ADMIN_USER
        self.admin_password = settings.KEYCLOAK_ADMIN_PASSWORD
        self.admin_token = None
    
    def get_admin_token(self):
        """Obtenir un token d'administration Keycloak"""
        try:
            token_url = f"{self.base_url}/realms/master/protocol/openid-connect/token"
            data = {
                'username': self.admin_username,
                'password': self.admin_password,
                'grant_type': 'password',
                'client_id': 'admin-cli'
            }
            
            response = requests.post(token_url, data=data, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.admin_token = token_data['access_token']
            return self.admin_token
            
        except Exception as e:
            logger.error(f"Erreur lors de l'obtention du token admin Keycloak: {e}")
            return None
    
    def create_user_in_keycloak(self, user_data):
        """Créer un utilisateur dans Keycloak"""
        try:
            if not self.admin_token:
                self.admin_token = self.get_admin_token()
                if not self.admin_token:
                    return False, "Impossible d'obtenir le token d'administration"
            
            # Préparer les données utilisateur pour Keycloak
            keycloak_user = {
                "username": user_data['username'],
                "email": user_data['email'],
                "firstName": user_data['first_name'],
                "lastName": user_data['last_name'],
                "enabled": True,
                "emailVerified": False,
                "credentials": [{
                    "type": "password",
                    "value": user_data['password'],
                    "temporary": False
                }],
                "attributes": {
                    "date_naissance": [user_data.get('date_naissance', '')],
                    "telephone": [user_data.get('telephone', '')]
                }
            }
            
            # URL pour créer l'utilisateur
            create_user_url = f"{self.base_url}/admin/realms/{self.realm}/users"
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(
                create_user_url,
                headers=headers,
                json=keycloak_user,
                timeout=10
            )
            
            if response.status_code == 201:
                # Récupérer l'ID de l'utilisateur créé
                user_id = response.headers.get('Location', '').split('/')[-1]
                
                # Assigner le rôle
                role_assigned = self.assign_role_to_user(user_id, user_data['role'])
                if role_assigned:
                    return True, user_id
                else:
                    return False, "Utilisateur créé mais échec de l'assignation du rôle"
            else:
                logger.error(f"Erreur création utilisateur Keycloak: {response.status_code} - {response.text}")
                return False, f"Erreur lors de la création: {response.text}"
                
        except Exception as e:
            logger.error(f"Erreur lors de la création d'utilisateur dans Keycloak: {e}")
            return False, str(e)
    
    def assign_role_to_user(self, user_id, role_name):
        """Assigner un rôle à un utilisateur dans Keycloak"""
        try:
            # Mapper les noms de rôles Django vers Keycloak
            role_mapping = {
                'medecin': 'medecin',
                'patient': 'patient',
                'admin': 'admin'
            }
            
            keycloak_role = role_mapping.get(role_name, role_name)
            
            # Obtenir l'ID du rôle
            roles_url = f"{self.base_url}/admin/realms/{self.realm}/roles"
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(roles_url, headers=headers, timeout=10)
            if response.status_code != 200:
                logger.error(f"Erreur lors de la récupération des rôles: {response.text}")
                return False
            
            roles = response.json()
            role_id = None
            
            for role in roles:
                if role['name'] == keycloak_role:
                    role_id = role['id']
                    break
            
            if not role_id:
                logger.error(f"Rôle {keycloak_role} non trouvé dans Keycloak")
                return False
            
            # Assigner le rôle à l'utilisateur
            assign_role_url = f"{self.base_url}/admin/realms/{self.realm}/users/{user_id}/role-mappings/realm"
            
            role_data = [{"id": role_id, "name": keycloak_role}]
            
            response = requests.post(
                assign_role_url,
                headers=headers,
                json=role_data,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info(f"Rôle {keycloak_role} assigné avec succès à l'utilisateur {user_id}")
                return True
            else:
                logger.error(f"Erreur lors de l'assignation du rôle: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'assignation du rôle: {e}")
            return False
    
    def verify_user_exists(self, username):
        """Vérifier si un utilisateur existe dans Keycloak"""
        try:
            if not self.admin_token:
                self.admin_token = self.get_admin_token()
                if not self.admin_token:
                    return False
            
            search_url = f"{self.base_url}/admin/realms/{self.realm}/users?username={username}&exact=true"
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                return len(users) > 0
            else:
                logger.error(f"Erreur lors de la vérification de l'utilisateur: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'utilisateur: {e}")
            return False 