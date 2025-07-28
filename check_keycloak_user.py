#!/usr/bin/env python
"""
Script pour vérifier si un utilisateur existe dans Keycloak
"""

import os
import sys
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.conf import settings

def get_keycloak_token():
    """Obtenir un token d'accès Keycloak"""
    token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.OIDC_REALM}/protocol/openid-connect/token"
    
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': settings.KEYCLOAK_ADMIN_USER,
        'password': settings.KEYCLOAK_ADMIN_PASSWORD,
    }
    
    try:
        response = requests.post(token_url, data=data, verify=False)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"❌ Erreur lors de l'obtention du token: {e}")
        return None

def find_user_in_keycloak(email):
    """Rechercher un utilisateur par email dans Keycloak"""
    token = get_keycloak_token()
    if not token:
        return None
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Recherche par email exact
    search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
    params = {'email': email, 'exact': 'true'}
    
    try:
        response = requests.get(search_url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        users = response.json()
        
        if users:
            return users[0]
        return None
    except Exception as e:
        print(f"❌ Erreur lors de la recherche: {e}")
        return None

def main():
    email = "rassoulmouhamd2@gmail.com"
    
    print(f"🔍 Recherche de l'utilisateur: {email}")
    print("=" * 50)
    
    user = find_user_in_keycloak(email)
    
    if user:
        print("✅ Utilisateur trouvé dans Keycloak:")
        print(f"   ID: {user.get('id')}")
        print(f"   Email: {user.get('email')}")
        print(f"   Username: {user.get('username')}")
        print(f"   Enabled: {user.get('enabled')}")
        print(f"   Email Verified: {user.get('emailVerified')}")
        print(f"   Required Actions: {user.get('requiredActions')}")
        
        # Vérifier les groupes
        if user.get('id'):
            group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user['id']}/groups"
            token = get_keycloak_token()
            headers = {'Authorization': f'Bearer {token}'}
            
            try:
                group_response = requests.get(group_url, headers=headers, verify=False)
                if group_response.status_code == 200:
                    groups = group_response.json()
                    print(f"   Groupes: {[g.get('name') for g in groups]}")
            except:
                print("   Groupes: Erreur lors de la récupération")
    else:
        print("❌ Utilisateur non trouvé dans Keycloak")

if __name__ == "__main__":
    main() 