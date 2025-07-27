#!/usr/bin/env python3
"""
Script pour vérifier la synchronisation d'un utilisateur spécifique
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

def check_user_in_keycloak(email, admin_token):
    """Vérifier un utilisateur dans Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                user_data = users[0]
                print(f"👤 Utilisateur Keycloak trouvé:")
                print(f"   ID: {user_data.get('id')}")
                print(f"   Username: {user_data.get('username')}")
                print(f"   Email: {user_data.get('email', 'NON DÉFINI ❌')}")
                print(f"   Prénom: {user_data.get('firstName', 'NON DÉFINI')}")
                print(f"   Nom: {user_data.get('lastName', 'NON DÉFINI')}")
                print(f"   Activé: {user_data.get('enabled')}")
                print(f"   Email vérifié: {user_data.get('emailVerified')}")
                return user_data
            else:
                print(f"❌ Utilisateur {email} non trouvé dans Keycloak")
                return None
        else:
            print(f"❌ Erreur recherche Keycloak: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur vérification utilisateur: {e}")
        return None

def test_last_user():
    """Tester le dernier utilisateur créé"""
    print("🔧 DIAGNOSTIC DU DERNIER UTILISATEUR CRÉÉ")
    print("=" * 60)
    
    # Récupérer le dernier utilisateur
    try:
        last_user = Utilisateur.objects.order_by('-date_creation').first()
        if not last_user:
            print("❌ Aucun utilisateur trouvé")
            return
            
        print(f"👤 Dernier utilisateur Django:")
        print(f"   Email: {last_user.email}")
        print(f"   Prénom: {last_user.prenom}")
        print(f"   Nom: {last_user.nom}")
        print(f"   Rôle: {last_user.role_autorise}")
        print(f"   Actif: {last_user.est_actif}")
        print(f"   Créé: {last_user.date_creation}")
        
        # Obtenir token admin Keycloak
        print(f"\n🔑 Connexion à Keycloak...")
        admin_token = get_keycloak_admin_token()
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return
        
        # Vérifier dans Keycloak
        print(f"\n🔍 Vérification dans Keycloak...")
        keycloak_user = check_user_in_keycloak(last_user.email, admin_token)
        
        # Analyser le résultat
        if not keycloak_user:
            print(f"\n❌ PROBLÈME: Utilisateur non trouvé dans Keycloak")
            print("🔧 Tentative de synchronisation...")
            success = KeycloakSyncService.ensure_user_complete_profile(last_user)
            if success:
                print("✅ Synchronisation réussie!")
                # Re-vérifier
                print(f"\n🔍 Re-vérification...")
                check_user_in_keycloak(last_user.email, admin_token)
            else:
                print("❌ Échec de la synchronisation")
        elif not keycloak_user.get('email'):
            print(f"\n❌ PROBLÈME: Email manquant dans Keycloak")
            print("🔧 Tentative de mise à jour...")
            success = KeycloakSyncService.ensure_user_complete_profile(last_user)
            if success:
                print("✅ Mise à jour réussie!")
                # Re-vérifier
                print(f"\n🔍 Re-vérification...")
                check_user_in_keycloak(last_user.email, admin_token)
            else:
                print("❌ Échec de la mise à jour")
        else:
            print("✅ Utilisateur correctement synchronisé!")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_last_user()
