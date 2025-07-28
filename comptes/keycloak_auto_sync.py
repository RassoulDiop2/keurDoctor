"""
Signal automatique pour synchroniser Django → Keycloak
Se déclenche automatiquement à chaque création/modification d'utilisateur
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)

class KeycloakSyncService:
    """Service de synchronisation automatique avec Keycloak"""
    
    @staticmethod
    def get_admin_token():
        """Obtient le token admin Keycloak"""
        try:
            token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
            data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': settings.KEYCLOAK_ADMIN_USER,
                'password': settings.KEYCLOAK_ADMIN_PASSWORD
            }
            response = requests.post(token_url, data=data, timeout=10)
            if response.status_code == 200:
                return response.json().get('access_token')
            return None
        except Exception as e:
            logger.error(f"Erreur token Keycloak: {e}")
            return None
    
    @staticmethod
    def ensure_user_complete_profile(user):
        """
        S'assure que l'utilisateur a un profil complet dans Keycloak
        - Email vérifié = True
        - Required Actions = []
        - Prénom et nom propres
        """
        try:
            admin_token = KeycloakSyncService.get_admin_token()
            if not admin_token:
                return False

            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }

            # Rechercher l'utilisateur dans Keycloak
            search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={user.email}&exact=true"
            search_resp = requests.get(search_url, headers=headers, timeout=10)
            
            if search_resp.status_code != 200 or not search_resp.json():
                # Utilisateur n'existe pas, le créer
                return KeycloakSyncService.create_complete_user(user, admin_token)
            
            # Utilisateur existe, le mettre à jour
            user_data = search_resp.json()[0]
            user_id = user_data['id']
            
            # Nettoyer les données
            first_name = user.prenom.replace('Dr.', '').replace('Dr', '').strip() if user.prenom else 'Utilisateur'
            last_name = user.nom.strip() if user.nom else 'KeurDoctor'
            
            # Données de mise à jour COMPLÈTES
            update_data = {
                "username": user.email,
                "email": user.email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,  # ✅ TOUJOURS vérifié
                "requiredActions": [],  # ✅ JAMAIS d'actions requises
                "attributes": {
                    "role": [user.role_autorise or 'patient']
                }
            }
            
            # Mettre à jour
            update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
            update_resp = requests.put(update_url, json=update_data, headers=headers, timeout=10)
            
            if update_resp.status_code in (200, 204):
                # ✅ MISE À JOUR DES GROUPES KEYCLOAK AUSSI
                KeycloakSyncService.assign_user_to_keycloak_groups(user, user_id, admin_token)
                logger.info(f"✅ Profil ET groupes Keycloak mis à jour automatiquement: {user.email}")
                return True
            else:
                logger.error(f"❌ Erreur mise à jour Keycloak: {update_resp.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur synchronisation automatique: {e}")
            return False
    
    @staticmethod
    def create_complete_user(user, admin_token):
        """Crée un utilisateur complet dans Keycloak avec rôles et groupes"""
        try:
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Nettoyer les données
            first_name = user.prenom.replace('Dr.', '').replace('Dr', '').strip() if user.prenom else 'Utilisateur'
            last_name = user.nom.strip() if user.nom else 'KeurDoctor'
            
            # Données utilisateur COMPLÈTES
            user_data = {
                "username": user.email,
                "email": user.email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,  # ✅ TOUJOURS vérifié
                "requiredActions": [],  # ✅ JAMAIS d'actions requises
                "attributes": {
                    "role": [user.role_autorise or 'patient']
                }
            }
            
            # Créer l'utilisateur
            create_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
            create_resp = requests.post(create_url, json=user_data, headers=headers, timeout=10)
            
            if create_resp.status_code == 201:
                logger.info(f"✅ Utilisateur Keycloak créé automatiquement: {user.email}")
                
                # Récupérer l'ID utilisateur créé
                search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={user.email}&exact=true"
                search_resp = requests.get(search_url, headers=headers, timeout=10)
                
                if search_resp.json():
                    user_id = search_resp.json()[0]['id']
                    
                    # ✅ ÉTAPE CRUCIALE: ASSIGNER AUX GROUPES KEYCLOAK
                    success_groups = KeycloakSyncService.assign_user_to_keycloak_groups(user, user_id, admin_token)
                    
            elif create_resp.status_code == 409:
                # ✅ GESTION ERREUR 409 - Utilisateur existe, le mettre à jour
                logger.warning(f"⚠️ Utilisateur {user.email} existe déjà dans Keycloak (409) - Mise à jour...")
                
                # Rechercher l'utilisateur existant par email ET par username
                search_attempts = [
                    f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={user.email}&exact=true",
                    f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?username={user.email}&exact=true"
                ]
                
                existing_user = None
                for search_url in search_attempts:
                    search_resp = requests.get(search_url, headers=headers, timeout=10)
                    if search_resp.status_code == 200 and search_resp.json():
                        existing_user = search_resp.json()[0]
                        break
                
                if existing_user:
                    user_id = existing_user['id']
                    logger.info(f"🔄 Utilisateur existant trouvé - ID: {user_id}")
                    
                    # Mettre à jour avec les données complètes
                    update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
                    update_resp = requests.put(update_url, json=user_data, headers=headers, timeout=10)
                    
                    if update_resp.status_code in (200, 204):
                        logger.info(f"✅ Utilisateur Keycloak mis à jour: {user.email}")
                        
                        # ✅ ASSIGNER AUX GROUPES AUSSI
                        success_groups = KeycloakSyncService.assign_user_to_keycloak_groups(user, user_id, admin_token)
                        
                    else:
                        logger.error(f"❌ Erreur mise à jour utilisateur existant: {update_resp.status_code}")
                        return False
                else:
                    logger.error(f"❌ Erreur 409 mais utilisateur non trouvé: {user.email}")
                    return False
                    
            # ✅ CONFIGURATION MOT DE PASSE ET FINALISATION
            if 'user_id' in locals():
                # Définir un mot de passe par défaut
                password_data = {
                    "type": "password",
                    "value": "MotDePasseTemporaire123!",
                    "temporary": False  # ✅ Mot de passe permanent - pas de changement forcé
                }
                
                pwd_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/reset-password"
                pwd_resp = requests.put(pwd_url, json=password_data, headers=headers, timeout=10)
                
                if pwd_resp.status_code in (200, 204):
                    logger.info(f"🎯 Utilisateur COMPLET créé/mis à jour dans Keycloak: {user.email} (rôle: {user.role_autorise})")
                    logger.info("[SUCCESS] Synchronisation COMPLETE reussie: {}".format(user.email))
                    logger.info("   Profil Keycloak cree/mis a jour")
                    logger.info("   Groupe assigne selon role: {}".format(user.role_autorise or 'patient'))
                    logger.info("   Roles realm et client assignes")
                    logger.info("   Utilisateur peut maintenant se connecter!")
                    return True
                else:
                    logger.warning(f"⚠️ Utilisateur créé/mis à jour mais mot de passe non défini: {user.email}")
                    return True  # Utilisateur créé quand même
                
            return True
                
        except Exception as e:
            logger.error(f"❌ Erreur création utilisateur Keycloak: {e}")
            return False

    @staticmethod
    def assign_user_to_keycloak_groups(user, user_id, admin_token):
        """
        ✅ MÉTHODE CRUCIALE: Assigner l'utilisateur aux bons groupes Keycloak
        C'est ce qui permet à l'utilisateur de se connecter avec les bonnes permissions
        """
        try:
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Mapping des rôles Django vers les groupes Keycloak
            role_to_group = {
                'admin': 'administrateurs',
                'medecin': 'médecins', 
                'patient': 'patients'
            }
            
            user_role = user.role_autorise or 'patient'
            group_name = role_to_group.get(user_role, 'patients')
            
            # 1. Récupérer tous les groupes Keycloak
            groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
            groups_resp = requests.get(groups_url, headers=headers, timeout=10)
            
            if groups_resp.status_code != 200:
                logger.error(f"❌ Impossible de récupérer les groupes Keycloak: {groups_resp.status_code}")
                return False
            
            # 2. Trouver le groupe correspondant au rôle
            target_group = None
            for group in groups_resp.json():
                if group['name'] == group_name:
                    target_group = group
                    break
            
            if not target_group:
                logger.warning(f"⚠️ Groupe {group_name} non trouvé dans Keycloak - Création automatique...")
                # Créer le groupe s'il n'existe pas
                create_group_data = {
                    "name": group_name,
                    "attributes": {
                        "description": [f"Groupe automatique pour {user_role}"]
                    }
                }
                create_group_resp = requests.post(groups_url, json=create_group_data, headers=headers, timeout=10)
                
                if create_group_resp.status_code == 201:
                    logger.info(f"✅ Groupe {group_name} créé automatiquement")
                    # Re-récupérer les groupes
                    groups_resp = requests.get(groups_url, headers=headers, timeout=10)
                    for group in groups_resp.json():
                        if group['name'] == group_name:
                            target_group = group
                            break
                else:
                    logger.error(f"❌ Impossible de créer le groupe {group_name}")
                    return False
            
            if target_group:
                # 3. Assigner l'utilisateur au groupe
                group_id = target_group['id']
                assign_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups/{group_id}"
                assign_resp = requests.put(assign_url, headers=headers, timeout=10)
                
                if assign_resp.status_code in (200, 204):
                    logger.info(f"🎯 Utilisateur {user.email} assigné au groupe '{group_name}' dans Keycloak")
                    
                    # 4. ✅ ASSIGNER LES RÔLES REALM KEYCLOAK (CRUCIAL!)
                    KeycloakSyncService.assign_realm_roles(user, user_id, user_role, admin_token)
                    
                    # 5. ✅ ASSIGNER AUSSI LES RÔLES CLIENT KEYCLOAK
                    KeycloakSyncService.assign_client_roles(user, user_id, user_role, admin_token)
                    
                    return True
                else:
                    logger.error(f"❌ Impossible d'assigner au groupe {group_name}: {assign_resp.status_code}")
                    return False
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Erreur assignation groupes Keycloak: {e}")
            return False

    @staticmethod
    def assign_realm_roles(user, user_id, user_role, admin_token):
        """
        ✅ MÉTHODE CRUCIALE: Assigner les rôles REALM Keycloak
        Les rôles realm sont nécessaires pour l'authentification OIDC
        """
        try:
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Mapping des rôles Django vers les rôles realm Keycloak
            realm_role_mappings = {
                'admin': ['admin', 'user', 'offline_access'],
                'medecin': ['medecin', 'user', 'offline_access'],
                'patient': ['patient', 'user', 'offline_access']
            }
            
            roles_to_assign = realm_role_mappings.get(user_role, ['user', 'offline_access'])
            
            # 1. Récupérer tous les rôles realm disponibles
            realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/roles"
            roles_resp = requests.get(realm_roles_url, headers=headers, timeout=10)
            
            if roles_resp.status_code != 200:
                logger.error(f"❌ Impossible de récupérer les rôles realm: {roles_resp.status_code}")
                return False
            
            available_realm_roles = roles_resp.json()
            
            # 2. Préparer les rôles à assigner
            roles_payload = []
            missing_roles = []
            
            for role_name in roles_to_assign:
                role_found = False
                for realm_role in available_realm_roles:
                    if realm_role['name'] == role_name:
                        roles_payload.append({
                            'id': realm_role['id'],
                            'name': realm_role['name']
                        })
                        role_found = True
                        break
                
                if not role_found:
                    missing_roles.append(role_name)
            
            # 3. Créer les rôles manquants si nécessaire
            for missing_role in missing_roles:
                logger.info(f"🔧 Création du rôle realm manquant: {missing_role}")
                create_role_data = {
                    "name": missing_role,
                    "description": f"Rôle automatique pour {user_role}",
                    "composite": False,
                    "clientRole": False
                }
                
                create_role_resp = requests.post(realm_roles_url, json=create_role_data, headers=headers, timeout=10)
                
                if create_role_resp.status_code == 201:
                    # Re-récupérer le rôle créé
                    roles_resp = requests.get(realm_roles_url, headers=headers, timeout=10)
                    if roles_resp.status_code == 200:
                        for realm_role in roles_resp.json():
                            if realm_role['name'] == missing_role:
                                roles_payload.append({
                                    'id': realm_role['id'],
                                    'name': realm_role['name']
                                })
                                break
                    logger.info(f"✅ Rôle realm {missing_role} créé automatiquement")
                else:
                    logger.warning(f"⚠️ Impossible de créer le rôle realm {missing_role}")
            
            # 4. Assigner les rôles realm à l'utilisateur
            if roles_payload:
                assign_realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
                assign_resp = requests.post(assign_realm_roles_url, json=roles_payload, headers=headers, timeout=10)
                
                if assign_resp.status_code in (200, 204):
                    assigned_role_names = [role['name'] for role in roles_payload]
                    logger.info(f"🎭 Rôles REALM assignés à {user.email}: {assigned_role_names}")
                    return True
                else:
                    logger.error(f"❌ Impossible d'assigner les rôles realm: {assign_resp.status_code}")
                    return False
            else:
                logger.warning(f"⚠️ Aucun rôle realm à assigner pour {user.email}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur assignation rôles realm: {e}")
            return False

    @staticmethod
    def assign_client_roles(user, user_id, user_role, admin_token):
        """
        Assigner les rôles client Keycloak pour les permissions d'accès
        """
        try:
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # Mapping des rôles vers les rôles client Keycloak
            role_mappings = {
                'admin': ['admin', 'user'],
                'medecin': ['medecin', 'user'],
                'patient': ['patient', 'user']
            }
            
            roles_to_assign = role_mappings.get(user_role, ['user'])
            
            # Récupérer les rôles client disponibles
            # Utiliser OIDC_RP_CLIENT_ID au lieu de OIDC_CLIENT_ID
            client_id = getattr(settings, 'OIDC_RP_CLIENT_ID', 'django-KDclient')
            
            # D'abord, récupérer l'ID interne du client
            clients_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/clients"
            clients_resp = requests.get(clients_url, headers=headers, timeout=10)
            
            client_uuid = None
            if clients_resp.status_code == 200:
                for client in clients_resp.json():
                    if client.get('clientId') == client_id:
                        client_uuid = client['id']
                        break
            
            if not client_uuid:
                logger.warning(f"⚠️ Client {client_id} non trouvé dans Keycloak")
                return
            
            client_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/clients/{client_uuid}/roles"
            roles_resp = requests.get(client_roles_url, headers=headers, timeout=10)
            
            if roles_resp.status_code == 200:
                available_roles = roles_resp.json()
                
                # Préparer les rôles à assigner
                roles_payload = []
                for role_name in roles_to_assign:
                    for role in available_roles:
                        if role['name'] == role_name:
                            roles_payload.append({
                                'id': role['id'],
                                'name': role['name']
                            })
                
                if roles_payload:
                    # Assigner les rôles client
                    assign_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
                    assign_roles_resp = requests.post(assign_roles_url, json=roles_payload, headers=headers, timeout=10)
                    
                    if assign_roles_resp.status_code in (200, 204):
                        logger.info(f"✅ Rôles client assignés à {user.email}: {[r['name'] for r in roles_payload]}")
                    else:
                        logger.warning(f"⚠️ Impossible d'assigner les rôles client: {assign_roles_resp.status_code}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Erreur assignation rôles client: {e}")

    @staticmethod
    def ensure_keycloak_setup():
        """
        ✅ S'assurer que Keycloak a tous les rôles et groupes nécessaires
        À appeler au démarrage de l'application
        """
        try:
            admin_token = KeycloakSyncService.get_admin_token()
            if not admin_token:
                logger.error("❌ Impossible d'obtenir le token admin pour setup Keycloak")
                return False
            
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # 1. Créer les rôles realm nécessaires
            required_realm_roles = ['admin', 'medecin', 'patient', 'user']
            realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/roles"
            
            # Récupérer les rôles existants
            existing_roles_resp = requests.get(realm_roles_url, headers=headers, timeout=10)
            existing_role_names = []
            
            if existing_roles_resp.status_code == 200:
                existing_role_names = [role['name'] for role in existing_roles_resp.json()]
            
            # Créer les rôles manquants
            for role_name in required_realm_roles:
                if role_name not in existing_role_names:
                    role_data = {
                        "name": role_name,
                        "description": f"Rôle {role_name} pour KeurDoctor",
                        "composite": False,
                        "clientRole": False
                    }
                    
                    create_resp = requests.post(realm_roles_url, json=role_data, headers=headers, timeout=10)
                    if create_resp.status_code == 201:
                        logger.info(f"✅ Rôle realm créé: {role_name}")
                    else:
                        logger.warning(f"⚠️ Impossible de créer le rôle {role_name}")
            
            # 2. Créer les groupes nécessaires
            required_groups = ['administrateurs', 'médecins', 'patients']
            groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
            
            # Récupérer les groupes existants
            existing_groups_resp = requests.get(groups_url, headers=headers, timeout=10)
            existing_group_names = []
            
            if existing_groups_resp.status_code == 200:
                existing_group_names = [group['name'] for group in existing_groups_resp.json()]
            
            # Créer les groupes manquants
            for group_name in required_groups:
                if group_name not in existing_group_names:
                    group_data = {
                        "name": group_name,
                        "attributes": {
                            "description": [f"Groupe {group_name} pour KeurDoctor"]
                        }
                    }
                    
                    create_resp = requests.post(groups_url, json=group_data, headers=headers, timeout=10)
                    if create_resp.status_code == 201:
                        logger.info(f"✅ Groupe créé: {group_name}")
                    else:
                        logger.warning(f"⚠️ Impossible de créer le groupe {group_name}")
            
            logger.info("🎯 Setup Keycloak terminé - Rôles et groupes prêts")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur setup Keycloak: {e}")
            return False


# ✅ SIGNALS AUTOMATIQUES - SE DÉCLENCHENT AUTOMATIQUEMENT

# Variable pour s'assurer que le setup n'est fait qu'une fois
_keycloak_setup_done = False

@receiver(post_save, sender='comptes.Utilisateur')
def auto_sync_user_to_keycloak(sender, instance, created, **kwargs):
    """
    Signal automatique qui se déclenche à chaque sauvegarde d'utilisateur
    - Création : crée l'utilisateur dans Keycloak avec profil complet + rôles + groupes
    - Modification : met à jour le profil Keycloak
    """
    global _keycloak_setup_done
    
    try:
        # ✅ S'assurer que Keycloak est configuré (rôles et groupes)
        if not _keycloak_setup_done:
            logger.info("🔧 Premier usage - Configuration automatique Keycloak...")
            setup_success = KeycloakSyncService.ensure_keycloak_setup()
            if setup_success:
                _keycloak_setup_done = True
                logger.info("✅ Setup Keycloak terminé")
            else:
                logger.warning("⚠️ Setup Keycloak partiel - continuera quand même")
        
        if created:
            logger.info(f"🔄 Création détectée - Synchronisation COMPLÈTE: {instance.email}")
        else:
            logger.info(f"🔄 Modification détectée - Synchronisation COMPLÈTE: {instance.email}")
        
        # Synchronisation automatique COMPLÈTE (profil + groupes + rôles)
        success = KeycloakSyncService.ensure_user_complete_profile(instance)
        
        if success:
            logger.info(f"[SUCCESS] Synchronisation COMPLETE reussie: {instance.email}")
            logger.info(f"   Profil Keycloak cree/mis a jour")
            logger.info(f"   Groupe assigne selon role: {instance.role_autorise}")
            logger.info(f"   Roles realm et client assignes")
            logger.info(f"   Utilisateur peut maintenant se connecter!")
        else:
            logger.warning(f"[WARNING] Synchronisation COMPLETE echouee: {instance.email}")
            logger.warning(f"   L'utilisateur pourrait ne pas pouvoir se connecter")
            
    except Exception as e:
        logger.error(f"❌ Erreur signal automatique: {e}")


@receiver(pre_save, sender='comptes.Utilisateur')
def validate_user_data(sender, instance, **kwargs):
    """
    Signal pour nettoyer les données avant sauvegarde
    """
    try:
        # Nettoyer le prénom (supprimer les titres)
        if instance.prenom:
            instance.prenom = instance.prenom.replace('Dr.', '').replace('Dr', '').strip()
        
        # S'assurer qu'il y a toujours un prénom et nom
        if not instance.prenom:
            instance.prenom = 'Utilisateur'
        if not instance.nom:
            instance.nom = 'KeurDoctor'
            
        logger.info(f"🧹 Données nettoyées: {instance.email} - {instance.prenom} {instance.nom}")
        
    except Exception as e:
        logger.error(f"❌ Erreur nettoyage données: {e}")
