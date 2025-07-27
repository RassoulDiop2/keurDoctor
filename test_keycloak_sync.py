#!/usr/bin/env python3
"""
Script pour tester et corriger la synchronisation Keycloak d'un utilisateur
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

def test_user_sync(email):
    """Tester la synchronisation d'un utilisateur"""
    print(f"🔍 TEST SYNCHRONISATION UTILISATEUR: {email}")
    print("=" * 60)
    
    # 1. Vérifier l'utilisateur Django
    try:
        user = Utilisateur.objects.get(email=email)
        print(f"👤 Utilisateur Django trouvé:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
        print(f"   Actif: {user.est_actif}")
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {email} non trouvé dans Django")
        return
    
    # 2. Obtenir token admin Keycloak
    print(f"\n🔑 Connexion à Keycloak...")
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin Keycloak")
        return
    
    # 3. Vérifier dans Keycloak
    print(f"\n🔍 Vérification dans Keycloak...")
    keycloak_user = check_user_in_keycloak(email, admin_token)
    
    # 4. Forcer la synchronisation si problème
    if not keycloak_user or not keycloak_user.get('email'):
        print(f"\n🔧 PROBLÈME DÉTECTÉ - Forçage de la synchronisation...")
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        if success:
            print("✅ Synchronisation forcée réussie!")
            # Re-vérifier
            print(f"\n🔍 Re-vérification après synchronisation...")
            check_user_in_keycloak(email, admin_token)
        else:
            print("❌ Échec de la synchronisation forcée")
    else:
        print("✅ Utilisateur correctement synchronisé dans Keycloak")

def main():
    print("🔧 DIAGNOSTIC SYNCHRONISATION KEYCLOAK")
    print("=" * 60)
    
    # Lister les utilisateurs récents
    print("📋 Derniers utilisateurs créés:")
    recent_users = Utilisateur.objects.order_by('-date_creation')[:5]
    for i, user in enumerate(recent_users, 1):
        print(f"{i}. {user.email} ({user.role_autorise}) - {user.date_creation}")
    
    # Demander quel utilisateur tester
    try:
        choice = input("\nEntrez le numéro de l'utilisateur à tester (ou email direct): ").strip()
        
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(recent_users):
                test_email = recent_users[idx].email
            else:
                print("❌ Numéro invalide")
                return
        else:
            test_email = choice
        
        test_user_sync(test_email)
        
    except KeyboardInterrupt:
        print("\n❌ Test annulé")
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    main() 