#!/usr/bin/env python
"""
Script de diagnostic pour tester la connexion Keycloak
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

def test_keycloak_connection():
    """Tester la connexion à Keycloak"""
    
    print("=== DIAGNOSTIC KEYCLOAK ===")
    print(f"URL Keycloak: {settings.KEYCLOAK_SERVER_URL}")
    print(f"Realm: {settings.OIDC_REALM}")
    print(f"Client ID: {settings.OIDC_RP_CLIENT_ID}")
    print(f"Admin Client ID: {settings.KEYCLOAK_ADMIN_CLIENT_ID}")
    
    # Test 1: Vérifier si Keycloak est accessible
    print("\n1. Test d'accessibilité Keycloak...")
    try:
        response = requests.get(f"{settings.KEYCLOAK_SERVER_URL}/health", timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Keycloak est accessible")
        else:
            print("   ⚠️ Keycloak répond mais avec un statut inattendu")
    except Exception as e:
        print(f"   ❌ Impossible d'accéder à Keycloak: {e}")
        return
    
    # Test 2: Vérifier le realm
    print("\n2. Test du realm...")
    try:
        realm_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/{settings.OIDC_REALM}"
        response = requests.get(realm_url, timeout=5)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Realm trouvé")
        else:
            print("   ❌ Realm introuvable")
            print(f"   URL testée: {realm_url}")
    except Exception as e:
        print(f"   ❌ Erreur lors du test du realm: {e}")
    
    # Test 3: Essayer d'obtenir un token avec admin-cli
    print("\n3. Test d'authentification admin-cli...")
    try:
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': settings.KEYCLOAK_ADMIN_CLIENT_ID,
            'client_secret': settings.KEYCLOAK_ADMIN_CLIENT_SECRET
        }
        
        print(f"   URL: {token_url}")
        print(f"   Client ID: {settings.KEYCLOAK_ADMIN_CLIENT_ID}")
        print(f"   Client Secret: '{settings.KEYCLOAK_ADMIN_CLIENT_SECRET}'")
        
        response = requests.post(token_url, data=data, timeout=10)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("   ✅ Token obtenu avec succès")
            print(f"   Token type: {token_data.get('token_type')}")
            print(f"   Expires in: {token_data.get('expires_in')} secondes")
        else:
            print(f"   ❌ Erreur d'authentification: {response.status_code}")
            print(f"   Réponse: {response.text}")
            
            # Essayer avec password grant
            print("\n4. Test avec password grant...")
            data_password = {
                'grant_type': 'password',
                'client_id': settings.KEYCLOAK_ADMIN_CLIENT_ID,
                'username': settings.KEYCLOAK_ADMIN_USER,
                'password': settings.KEYCLOAK_ADMIN_PASSWORD
            }
            
            response2 = requests.post(token_url, data=data_password, timeout=10)
            print(f"   Status: {response2.status_code}")
            
            if response2.status_code == 200:
                token_data = response2.json()
                print("   ✅ Token obtenu avec password grant")
                return token_data['access_token']
            else:
                print(f"   ❌ Erreur avec password grant: {response2.status_code}")
                print(f"   Réponse: {response2.text}")
                
    except Exception as e:
        print(f"   ❌ Exception lors du test d'authentification: {e}")
    
    return None

def test_admin_api_with_token(token):
    """Tester l'API admin avec un token"""
    if not token:
        print("\n❌ Pas de token disponible pour tester l'API admin")
        return
    
    print("\n5. Test de l'API admin...")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Tester la récupération des groupes
    try:
        group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
        response = requests.get(group_url, headers=headers, timeout=10)
        
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            groups = response.json()
            print(f"   ✅ API admin fonctionnelle - {len(groups)} groupes trouvés")
            for group in groups:
                print(f"     - {group['name']} (ID: {group['id']})")
        else:
            print(f"   ❌ Erreur API admin: {response.status_code}")
            print(f"   Réponse: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception lors du test API admin: {e}")

if __name__ == "__main__":
    token = test_keycloak_connection()
    test_admin_api_with_token(token) 