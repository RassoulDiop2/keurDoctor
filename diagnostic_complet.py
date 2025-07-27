#!/usr/bin/env python3
"""
Script pour tester la création d'utilisateur avec Django serveur actif
"""
import os
import sys
import requests
import json
from datetime import datetime

def test_user_creation_api():
    """Test de création d'utilisateur via l'API d'administration"""
    
    print("🔧 TEST CRÉATION UTILISATEUR AVEC SERVEUR ACTIF")
    print("=" * 60)
    
    # Configuration
    django_admin_url = "http://127.0.0.1:8000/admin/"
    test_email = f"test.sync.{datetime.now().strftime('%H%M%S')}@example.com"
    
    print(f"📧 Email de test: {test_email}")
    
    # Vérifier que Django répond
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=5)
        print(f"✅ Serveur Django accessible (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Serveur Django non accessible: {e}")
        return False
    
    # Vérifier Keycloak
    try:
        response = requests.get("http://localhost:8080/realms/KeurDoctorSecure", timeout=5)
        print(f"✅ Keycloak accessible (status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"❌ Keycloak non accessible: {e}")
        return False
    
    # Test de l'endpoint admin
    try:
        response = requests.get(django_admin_url, timeout=5, allow_redirects=False)
        if response.status_code in [200, 302]:
            print(f"✅ Interface admin accessible")
        else:
            print(f"⚠️  Interface admin status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ Interface admin non accessible: {e}")
    
    print(f"\n🎯 INSTRUCTIONS POUR TEST MANUEL:")
    print(f"1. Ouvrir: {django_admin_url}")
    print(f"2. Se connecter avec superuser")
    print(f"3. Aller dans Comptes → Utilisateurs → Ajouter")
    print(f"4. Créer utilisateur avec email: {test_email}")
    print(f"5. Vérifier que l'utilisateur peut se connecter")
    
    return True

def check_keycloak_token():
    """Vérifier si on peut obtenir un token Keycloak"""
    
    print(f"\n🔑 TEST CONNEXION KEYCLOAK ADMIN")
    print("-" * 40)
    
    try:
        token_url = "http://localhost:8080/realms/master/protocol/openid-connect/token"
        token_data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin'
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        if response.status_code == 200:
            token_info = response.json()
            print(f"✅ Token admin obtenu")
            print(f"   Type: {token_info.get('token_type')}")
            print(f"   Expire dans: {token_info.get('expires_in')}s")
            return token_info['access_token']
        else:
            print(f"❌ Erreur token: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur connexion Keycloak: {e}")
        return None

def search_user_in_keycloak(email, admin_token):
    """Rechercher un utilisateur dans Keycloak"""
    
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"http://localhost:8080/admin/realms/KeurDoctorSecure/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        else:
            print(f"❌ Erreur recherche: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur recherche utilisateur: {e}")
        return None

def main():
    print("🚀 DIAGNOSTIC SYSTÈME COMPLET")
    print("=" * 60)
    
    # Test de base
    if not test_user_creation_api():
        return
    
    # Test Keycloak
    admin_token = check_keycloak_token()
    if admin_token:
        print(f"\n✅ Système prêt pour les tests!")
        print(f"\n📋 ÉTAPES DE TEST RECOMMANDÉES:")
        print(f"1. Créer un utilisateur via l'interface admin Django")
        print(f"2. Vérifier la synchronisation automatique Keycloak")
        print(f"3. Tester la connexion de l'utilisateur")
        
        # Proposer de rechercher un utilisateur existant
        email_to_search = "admin@keurdoctor.sn"  # Email par défaut
        print(f"\n🔍 Test recherche utilisateur existant: {email_to_search}")
        user_data = search_user_in_keycloak(email_to_search, admin_token)
        if user_data:
            print(f"✅ Utilisateur trouvé dans Keycloak:")
            print(f"   Email: {user_data.get('email', 'NON DÉFINI')}")
            print(f"   Username: {user_data.get('username')}")
            print(f"   Actif: {user_data.get('enabled')}")
        else:
            print(f"❌ Utilisateur {email_to_search} non trouvé dans Keycloak")
    else:
        print(f"\n❌ Problème de connexion Keycloak")
    
    print(f"\n✅ Diagnostic terminé")

if __name__ == "__main__":
    main()
