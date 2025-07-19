#!/usr/bin/env python
"""
Script pour diagnostiquer la recherche d'utilisateur dans Keycloak
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.conf import settings
import requests
import json

def get_keycloak_admin_token(keycloak_url):
    """Obtenir le token admin Keycloak"""
    try:
        token_url = f"{keycloak_url}/realms/master/protocol/openid-connect/token"
        data = {
            'grant_type': 'password',
            'client_id': settings.KEYCLOAK_ADMIN_CLIENT_ID,
            'username': settings.KEYCLOAK_ADMIN_USER,
            'password': settings.KEYCLOAK_ADMIN_PASSWORD
        }
        
        response = requests.post(token_url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Erreur lors de l'obtention du token: {response.status_code}")
            print(f"Réponse: {response.text}")
            return None
    except Exception as e:
        print(f"Exception lors de l'obtention du token: {e}")
        return None

def debug_user_search():
    """Diagnostiquer la recherche d'utilisateur"""
    
    print("=== DIAGNOSTIC RECHERCHE UTILISATEUR ===")
    
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return
            
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Test 1: Rechercher tous les utilisateurs
        print("\n1. Recherche de tous les utilisateurs...")
        all_users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        all_users_resp = requests.get(all_users_url, headers=headers)
        
        if all_users_resp.status_code == 200:
            all_users = all_users_resp.json()
            print(f"   ✅ {len(all_users)} utilisateurs trouvés dans Keycloak")
            for user in all_users:
                email = user.get('email', 'Pas d\'email')
                username = user.get('username', 'Pas de username')
                print(f"     - {email} (Username: {username}, ID: {user['id']})")
        else:
            print(f"   ❌ Erreur: {all_users_resp.status_code}")
            return
        
        # Test 2: Rechercher l'utilisateur spécifique
        print("\n2. Recherche de l'utilisateur moustaf@keurdoctor.com...")
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email=moustaf@keurdoctor.com"
        search_resp = requests.get(search_url, headers=headers)
        
        print(f"   URL: {search_url}")
        print(f"   Status: {search_resp.status_code}")
        
        if search_resp.status_code == 200:
            users = search_resp.json()
            print(f"   Résultats: {len(users)} utilisateur(s) trouvé(s)")
            
            if users:
                user = users[0]
                print(f"   ✅ Utilisateur trouvé:")
                print(f"     - ID: {user['id']}")
                print(f"     - Email: {user['email']}")
                print(f"     - Username: {user.get('username', 'N/A')}")
                print(f"     - Prénom: {user.get('firstName', 'N/A')}")
                print(f"     - Nom: {user.get('lastName', 'N/A')}")
                print(f"     - Activé: {user.get('enabled', 'N/A')}")
                
                # Vérifier les groupes
                print(f"\n3. Groupes de l'utilisateur...")
                user_groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user['id']}/groups"
                user_groups_resp = requests.get(user_groups_url, headers=headers)
                
                if user_groups_resp.status_code == 200:
                    user_groups = user_groups_resp.json()
                    print(f"   Groupes actuels: {[g['name'] for g in user_groups]}")
                else:
                    print(f"   ❌ Erreur récupération groupes: {user_groups_resp.status_code}")
                    
            else:
                print("   ❌ Aucun utilisateur trouvé avec cet email")
        else:
            print(f"   ❌ Erreur recherche: {search_resp.status_code}")
            print(f"   Réponse: {search_resp.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    debug_user_search() 