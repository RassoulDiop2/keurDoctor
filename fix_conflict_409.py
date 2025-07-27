#!/usr/bin/env python3
"""
Script pour résoudre définitivement les conflits Keycloak 409
"""
import os
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
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
        return None
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return None

def find_conflicting_user(email, admin_token):
    """Trouver l'utilisateur en conflit dans Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        # Recherche par email exact
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]
        
        # Recherche par username
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?username={email}&exact=true"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            if users:
                return users[0]
        
        # Recherche générale
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?search={email}"
        response = requests.get(search_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            users = response.json()
            for user in users:
                if user.get('email') == email or user.get('username') == email:
                    return user
        
        return None
        
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        return None

def delete_conflicting_user(user_id, admin_token):
    """Supprimer l'utilisateur en conflit"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        delete_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        response = requests.delete(delete_url, headers=headers, timeout=10)
        return response.status_code == 204
        
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        return False

def fix_conflict_409(email):
    """Résoudre le conflit 409 pour un utilisateur"""
    
    print(f"🔧 RÉSOLUTION CONFLIT 409: {email}")
    print("=" * 60)
    
    # 1. Obtenir token admin
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return False
    
    # 2. Trouver l'utilisateur en conflit
    print("🔍 Recherche de l'utilisateur en conflit...")
    conflicting_user = find_conflicting_user(email, admin_token)
    
    if conflicting_user:
        print(f"✅ Utilisateur en conflit trouvé:")
        print(f"   ID: {conflicting_user.get('id')}")
        print(f"   Username: {conflicting_user.get('username')}")
        print(f"   Email: {conflicting_user.get('email', 'VIDE')}")
        print(f"   Prénom: {conflicting_user.get('firstName', 'VIDE')}")
        print(f"   Nom: {conflicting_user.get('lastName', 'VIDE')}")
        
        # 3. Supprimer l'utilisateur en conflit
        print(f"\n🗑️  Suppression de l'utilisateur en conflit...")
        if delete_conflicting_user(conflicting_user['id'], admin_token):
            print("✅ Utilisateur en conflit supprimé avec succès")
            
            # 4. Forcer la re-synchronisation
            print(f"\n🔄 Re-synchronisation de l'utilisateur...")
            try:
                user = Utilisateur.objects.get(email=email)
                from comptes.keycloak_auto_sync import KeycloakSyncService
                
                success = KeycloakSyncService.ensure_user_complete_profile(user)
                if success:
                    print("✅ Re-synchronisation réussie!")
                    return True
                else:
                    print("❌ Échec de la re-synchronisation")
                    return False
                    
            except Exception as e:
                print(f"❌ Erreur re-synchronisation: {e}")
                return False
        else:
            print("❌ Échec de la suppression")
            return False
    else:
        print("⚠️  Aucun utilisateur en conflit trouvé")
        return False

def main():
    print("🚀 RÉSOLVEUR DE CONFLITS KEYCLOAK 409")
    print("=" * 60)
    
    # Utilisateur problématique identifié
    problematic_email = "mouharassoulmd@gmail.com"
    
    print(f"🎯 Résolution du conflit pour: {problematic_email}")
    
    success = fix_conflict_409(problematic_email)
    
    if success:
        print(f"\n✅ CONFLIT RÉSOLU!")
        print("L'utilisateur peut maintenant être synchronisé correctement")
        print("Testez en créant un nouvel utilisateur via l'interface admin")
    else:
        print(f"\n❌ ÉCHEC DE LA RÉSOLUTION")
        print("Vérifiez manuellement dans l'interface Keycloak")

if __name__ == "__main__":
    main()
