#!/usr/bin/env python3
"""
Script pour diagnostiquer pourquoi la synchronisation Keycloak échoue
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
import traceback
import logging

# Configuration logging détaillé
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnose_keycloak_connection():
    """Diagnostic de la connexion Keycloak"""
    
    print("🔍 DIAGNOSTIC CONNEXION KEYCLOAK")
    print("=" * 60)
    
    # Test 1: Keycloak accessible
    try:
        response = requests.get("http://localhost:8080/", timeout=5)
        print(f"✅ Keycloak serveur accessible (status: {response.status_code})")
    except Exception as e:
        print(f"❌ Keycloak serveur inaccessible: {e}")
        return False
    
    # Test 2: Token admin
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
            print(f"✅ Token admin obtenu")
            return response.json()['access_token']
        else:
            print(f"❌ Erreur token admin: {response.status_code}")
            print(f"   Réponse: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur connexion admin: {e}")
        return False

def diagnose_user_creation_process(email):
    """Simuler le processus de création d'utilisateur"""
    
    print(f"\n🧪 SIMULATION CRÉATION UTILISATEUR: {email}")
    print("=" * 60)
    
    try:
        # Récupérer l'utilisateur Django
        user = Utilisateur.objects.get(email=email)
        print(f"✅ Utilisateur Django trouvé:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
        
        # Test synchronisation détaillée
        print(f"\n🔄 Test synchronisation Keycloak...")
        print("=" * 40)
        
        # Activer le logging détaillé
        import logging
        logging.getLogger('comptes.keycloak_auto_sync').setLevel(logging.DEBUG)
        logging.getLogger('urllib3.connectionpool').setLevel(logging.DEBUG)
        
        # Forcer la synchronisation
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        
        if success:
            print("✅ Synchronisation réussie!")
        else:
            print("❌ Synchronisation échouée!")
            
        return success
        
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {email} non trouvé dans Django")
        return False
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        traceback.print_exc()
        return False

def check_keycloak_realm_settings():
    """Vérifier les paramètres du realm Keycloak"""
    
    print(f"\n🔧 VÉRIFICATION PARAMÈTRES KEYCLOAK")
    print("=" * 60)
    
    admin_token = diagnose_keycloak_connection()
    if not admin_token:
        return False
    
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        
        # Vérifier le realm
        realm_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}"
        response = requests.get(realm_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            realm_data = response.json()
            print(f"✅ Realm '{settings.OIDC_REALM}' accessible")
            print(f"   Activé: {realm_data.get('enabled')}")
            print(f"   Vérification email: {realm_data.get('verifyEmail')}")
            print(f"   Connexion requise: {realm_data.get('loginWithEmailAllowed')}")
        else:
            print(f"❌ Erreur accès realm: {response.status_code}")
            return False
            
        # Vérifier les clients
        clients_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/clients"
        response = requests.get(clients_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            clients = response.json()
            django_client = next((c for c in clients if c['clientId'] == settings.OIDC_RP_CLIENT_ID), None)
            if django_client:
                print(f"✅ Client Django '{settings.OIDC_RP_CLIENT_ID}' trouvé")
                print(f"   Activé: {django_client.get('enabled')}")
            else:
                print(f"❌ Client Django '{settings.OIDC_RP_CLIENT_ID}' non trouvé")
                return False
        else:
            print(f"❌ Erreur accès clients: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification Keycloak: {e}")
        return False

def main():
    print("🚀 DIAGNOSTIC COMPLET - ÉCHECS KEYCLOAK")
    print("=" * 70)
    
    # 1. Vérifier la connexion Keycloak
    if not diagnose_keycloak_connection():
        print("\n❌ ARRÊT - Problème de connexion Keycloak de base")
        return
    
    # 2. Vérifier les paramètres Keycloak
    if not check_keycloak_realm_settings():
        print("\n❌ ARRÊT - Problème de configuration Keycloak")
        return
    
    # 3. Tester avec l'utilisateur problématique
    problematic_user = "mouharassoulmd@gmail.com"
    print(f"\n🎯 Test avec utilisateur problématique: {problematic_user}")
    success = diagnose_user_creation_process(problematic_user)
    
    # 4. Analyser les résultats
    print(f"\n" + "="*70)
    print("🏆 RÉSULTATS DU DIAGNOSTIC:")
    
    if success:
        print("✅ La synchronisation fonctionne maintenant!")
        print("   Le problème était probablement temporaire.")
    else:
        print("❌ La synchronisation échoue encore.")
        print("   Causes possibles:")
        print("   - Problème de réseau avec Keycloak")
        print("   - Configuration Keycloak incorrecte")
        print("   - Données utilisateur invalides")
        print("   - Problème de permissions Keycloak")
    
    print(f"\n📋 RECOMMANDATIONS:")
    print("1. Vérifiez les logs détaillés ci-dessus")
    print("2. Testez la création d'un nouvel utilisateur")
    print("3. Vérifiez la configuration Keycloak")

if __name__ == "__main__":
    main()
