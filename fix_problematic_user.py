#!/usr/bin/env python3
"""
Script pour forcer la synchronisation de l'utilisateur problématique
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.keycloak_auto_sync import KeycloakSyncService
import requests
from django.conf import settings

def get_keycloak_admin_token():
    """Obtenir le token admin Keycloak"""
    try:
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        token_data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': settings.KEYCLOAK_ADMIN_USER,
            'password': settings.KEYCLOAK_ADMIN_PASSWORD
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"❌ Erreur token Keycloak: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion Keycloak: {e}")
        return None

def find_user_in_keycloak(email, admin_token):
    """Rechercher un utilisateur dans Keycloak avec différents patterns"""
    
    headers = {'Authorization': f'Bearer {admin_token}'}
    
    # Pattern 1: Recherche par email exact
    try:
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]
    except Exception as e:
        print(f"⚠️ Erreur recherche par email: {e}")
    
    # Pattern 2: Recherche par username
    try:
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?username={email}&exact=true"
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]
    except Exception as e:
        print(f"⚠️ Erreur recherche par username: {e}")
    
    # Pattern 3: Recherche globale
    try:
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?search={email}"
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get('email') == email or user.get('username') == email:
                    return user
    except Exception as e:
        print(f"⚠️ Erreur recherche globale: {e}")
    
    return None

def delete_and_recreate_user(email, admin_token):
    """Supprimer et recréer un utilisateur dans Keycloak"""
    
    print(f"🗑️ Suppression de l'utilisateur existant dans Keycloak...")
    
    # Trouver l'utilisateur
    keycloak_user = find_user_in_keycloak(email, admin_token)
    if keycloak_user:
        user_id = keycloak_user['id']
        
        # Supprimer
        headers = {'Authorization': f'Bearer {admin_token}'}
        delete_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        try:
            response = requests.delete(delete_url, headers=headers, timeout=10)
            if response.status_code == 204:
                print(f"✅ Utilisateur supprimé de Keycloak")
                return True
            else:
                print(f"❌ Erreur suppression: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False
    else:
        print(f"⚠️ Utilisateur non trouvé dans Keycloak pour suppression")
        return True  # Pas besoin de supprimer s'il n'existe pas

def fix_problematic_user():
    """Réparer l'utilisateur problématique"""
    
    problematic_email = "mouharassoulmd@gmail.com"
    
    print(f"🔧 RÉPARATION UTILISATEUR PROBLÉMATIQUE")
    print("=" * 60)
    print(f"📧 Email: {problematic_email}")
    
    # 1. Vérifier l'utilisateur Django
    try:
        user = Utilisateur.objects.get(email=problematic_email)
        print(f"✅ Utilisateur Django trouvé:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {problematic_email} non trouvé dans Django")
        return False
    
    # 2. Obtenir token admin
    print(f"\n🔑 Connexion à Keycloak...")
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin Keycloak")
        return False
    
    # 3. Vérifier dans Keycloak
    print(f"\n🔍 Recherche dans Keycloak...")
    keycloak_user = find_user_in_keycloak(problematic_email, admin_token)
    
    if keycloak_user:
        print(f"⚠️ Utilisateur existant trouvé dans Keycloak:")
        print(f"   ID: {keycloak_user.get('id')}")
        print(f"   Username: {keycloak_user.get('username')}")
        print(f"   Email: {keycloak_user.get('email', 'NON DÉFINI ❌')}")
        
        # Supprimer l'ancien utilisateur
        if delete_and_recreate_user(problematic_email, admin_token):
            print(f"✅ Ancien utilisateur supprimé")
        else:
            print(f"❌ Échec suppression ancien utilisateur")
            return False
    else:
        print(f"ℹ️ Aucun utilisateur existant trouvé dans Keycloak")
    
    # 4. Forcer la re-synchronisation complète
    print(f"\n🔄 Re-synchronisation complète...")
    success = KeycloakSyncService.ensure_user_complete_profile(user)
    
    if success:
        print(f"✅ RE-SYNCHRONISATION RÉUSSIE!")
        
        # Vérifier le résultat
        print(f"\n🔍 Vérification finale...")
        final_check = find_user_in_keycloak(problematic_email, admin_token)
        if final_check and final_check.get('email'):
            print(f"✅ PROBLÈME RÉSOLU!")
            print(f"   Email dans Keycloak: {final_check.get('email')}")
            return True
        else:
            print(f"❌ L'email n'est toujours pas dans Keycloak")
            return False
    else:
        print(f"❌ ÉCHEC de la re-synchronisation")
        return False

def main():
    print("🚀 RÉPARATEUR UTILISATEUR PROBLÉMATIQUE")
    print("=" * 60)
    
    success = fix_problematic_user()
    
    if success:
        print(f"\n🎉 RÉPARATION TERMINÉE AVEC SUCCÈS!")
        print(f"L'utilisateur mouharassoulmd@gmail.com peut maintenant se connecter")
        print(f"L'alerte dans l'interface admin devrait disparaître")
    else:
        print(f"\n❌ ÉCHEC DE LA RÉPARATION")
        print(f"Vérifiez que Keycloak est accessible et les credentials corrects")

if __name__ == "__main__":
    main()
