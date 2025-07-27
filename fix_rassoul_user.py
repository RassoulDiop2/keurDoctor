#!/usr/bin/env python3
"""
Script pour réparer l'utilisateur rassoulmouhamed2@gmail.com dans Keycloak
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
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
            print(f"❌ Erreur token: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion: {e}")
        return None

def find_keycloak_user_by_username(username, admin_token):
    """Rechercher un utilisateur par username dans Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?username={username}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None
    except Exception as e:
        print(f"❌ Erreur recherche: {e}")
        return None

def update_keycloak_user_email(user_id, email, admin_token):
    """Mettre à jour l'email d'un utilisateur dans Keycloak"""
    try:
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        # Données à mettre à jour
        update_data = {
            'email': email,
            'emailVerified': True,
            'enabled': True
        }
        
        response = requests.put(update_url, json=update_data, headers=headers, timeout=10)
        if response.status_code == 204:
            return True
        else:
            print(f"❌ Erreur mise à jour: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")
        return False

def fix_rassoul_user():
    """Réparer spécifiquement l'utilisateur rassoulmouhamed2@gmail.com"""
    
    print("🔧 RÉPARATION UTILISATEUR RASSOUL")
    print("=" * 60)
    
    problematic_email = "rassoulmouhamed2@gmail.com"
    
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
    
    # 2. Obtenir token admin Keycloak
    print(f"\n🔑 Connexion à Keycloak...")
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return False
    
    # 3. Rechercher l'utilisateur dans Keycloak par username
    print(f"\n🔍 Recherche dans Keycloak...")
    keycloak_user = find_keycloak_user_by_username(problematic_email, admin_token)
    
    if keycloak_user:
        print(f"✅ Utilisateur Keycloak trouvé:")
        print(f"   ID: {keycloak_user.get('id')}")
        print(f"   Username: {keycloak_user.get('username')}")
        print(f"   Email actuel: {keycloak_user.get('email', 'NON DÉFINI')}")
        
        # 4. Mettre à jour l'email si manquant
        if not keycloak_user.get('email'):
            print(f"\n🔧 Email manquant - Mise à jour...")
            success = update_keycloak_user_email(
                keycloak_user['id'], 
                problematic_email, 
                admin_token
            )
            
            if success:
                print("✅ Email mis à jour avec succès!")
                return True
            else:
                print("❌ Échec de la mise à jour")
                return False
        else:
            print("✅ Email déjà présent")
            return True
    else:
        print(f"❌ Utilisateur non trouvé dans Keycloak")
        
        # Tenter une synchronisation complète
        print(f"\n🔄 Tentative de synchronisation complète...")
        from comptes.keycloak_auto_sync import KeycloakSyncService
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        
        if success:
            print("✅ Synchronisation complète réussie!")
            return True
        else:
            print("❌ Échec de la synchronisation")
            return False

def main():
    print("🚀 RÉPARATEUR UTILISATEUR RASSOUL")
    print("=" * 60)
    
    success = fix_rassoul_user()
    
    if success:
        print(f"\n🎉 RÉPARATION RÉUSSIE!")
        print("L'utilisateur rassoulmouhamed2@gmail.com devrait maintenant avoir son email dans Keycloak")
        print("Vérifiez l'interface Keycloak pour confirmer")
    else:
        print(f"\n❌ ÉCHEC DE LA RÉPARATION")
        print("Vérifiez les logs pour plus de détails")

if __name__ == "__main__":
    main()
