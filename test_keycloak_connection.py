#!/usr/bin/env python
"""
Script pour tester la connexion à Keycloak avec retry
"""

import os
import sys
import time
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.conf import settings

def test_keycloak_health():
    """Tester la santé de Keycloak"""
    health_url = f"{settings.KEYCLOAK_SERVER_URL}/health"
    
    try:
        response = requests.get(health_url, verify=False, timeout=10)
        print(f"🔍 Statut Keycloak: {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Erreur de connexion à Keycloak: {e}")
        return False

def get_keycloak_token_with_retry(max_attempts=5, delay=10):
    """Obtenir un token d'accès Keycloak avec retry"""
    token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.OIDC_REALM}/protocol/openid-connect/token"
    
    data = {
        'grant_type': 'password',
        'client_id': 'admin-cli',
        'username': settings.KEYCLOAK_ADMIN_USER,
        'password': settings.KEYCLOAK_ADMIN_PASSWORD,
    }
    
    for attempt in range(max_attempts):
        print(f"🔄 Tentative {attempt + 1}/{max_attempts} de connexion à Keycloak...")
        
        try:
            response = requests.post(token_url, data=data, verify=False, timeout=30)
            
            if response.status_code == 200:
                token_data = response.json()
                print("✅ Connexion à Keycloak réussie!")
                return token_data['access_token']
            else:
                print(f"❌ Erreur {response.status_code}: {response.text}")
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
        
        if attempt < max_attempts - 1:
            print(f"⏳ Attente de {delay} secondes avant la prochaine tentative...")
            time.sleep(delay)
    
    return None

def main():
    print("🔍 Test de connexion à Keycloak")
    print("=" * 50)
    
    # Test de santé
    print("1. Test de santé Keycloak...")
    if test_keycloak_health():
        print("✅ Keycloak répond")
    else:
        print("❌ Keycloak ne répond pas")
    
    # Test d'authentification
    print("\n2. Test d'authentification admin...")
    token = get_keycloak_token_with_retry()
    
    if token:
        print("✅ Authentification réussie!")
        
        # Test de recherche d'utilisateur
        print("\n3. Test de recherche d'utilisateur...")
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        params = {'email': 'rassoulmouhamd2@gmail.com', 'exact': 'true'}
        
        try:
            response = requests.get(search_url, headers=headers, params=params, verify=False)
            if response.status_code == 200:
                users = response.json()
                if users:
                    user = users[0]
                    print(f"✅ Utilisateur trouvé: {user.get('email')} (ID: {user.get('id')})")
                    print(f"   Enabled: {user.get('enabled')}")
                    print(f"   Email Verified: {user.get('emailVerified')}")
                    print(f"   Required Actions: {user.get('requiredActions')}")
                else:
                    print("❌ Utilisateur non trouvé")
            else:
                print(f"❌ Erreur de recherche: {response.status_code}")
        except Exception as e:
            print(f"❌ Erreur lors de la recherche: {e}")
    else:
        print("❌ Échec de l'authentification")

if __name__ == "__main__":
    main() 