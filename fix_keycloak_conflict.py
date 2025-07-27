#!/usr/bin/env python3
"""
Script pour diagnostiquer et corriger les conflits Keycloak
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
        else:
            print(f"❌ Erreur token: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Erreur connexion Keycloak: {e}")
        return None

def search_user_by_patterns(email, admin_token):
    """Rechercher un utilisateur avec différents patterns"""
    
    headers = {'Authorization': f'Bearer {admin_token}'}
    realm_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}"
    
    patterns_to_search = [
        email,  # Email exact
        email.split('@')[0],  # Partie avant @
        email.replace('@', '.'),  # @ remplacé par .
        email.replace('@', '_'),  # @ remplacé par _
    ]
    
    print(f"🔍 Recherche avec différents patterns...")
    
    for pattern in patterns_to_search:
        try:
            # Recherche par email
            search_url = f"{realm_url}/users?email={pattern}&exact=false"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    print(f"✅ Trouvé avec pattern '{pattern}':")
                    for user in users:
                        print(f"   ID: {user.get('id')}")
                        print(f"   Username: {user.get('username')}")
                        print(f"   Email: {user.get('email', 'NON DÉFINI')}")
                        print(f"   Prénom: {user.get('firstName', 'NON DÉFINI')}")
                        print(f"   Nom: {user.get('lastName', 'NON DÉFINI')}")
                        print(f"   Activé: {user.get('enabled')}")
                        print(f"   ---")
                        return user
            
            # Recherche par username
            search_url = f"{realm_url}/users?username={pattern}&exact=false"
            response = requests.get(search_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                users = response.json()
                if users:
                    print(f"✅ Trouvé par username avec pattern '{pattern}':")
                    for user in users:
                        print(f"   ID: {user.get('id')}")
                        print(f"   Username: {user.get('username')}")
                        print(f"   Email: {user.get('email', 'NON DÉFINI')}")
                        print(f"   ---")
                        return user
                        
        except Exception as e:
            print(f"⚠️  Erreur recherche pattern '{pattern}': {e}")
            continue
    
    return None

def fix_user_conflict(email):
    """Diagnostiquer et corriger le conflit utilisateur"""
    
    print(f"🔧 DIAGNOSTIC CONFLIT UTILISATEUR: {email}")
    print("=" * 60)
    
    # 1. Vérifier l'utilisateur Django
    try:
        user = Utilisateur.objects.get(email=email)
        print(f"✅ Utilisateur Django:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {email} non trouvé dans Django")
        return False
    
    # 2. Obtenir token admin
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return False
    
    # 3. Rechercher avec différents patterns
    existing_user = search_user_by_patterns(email, admin_token)
    
    if existing_user:
        print(f"\n🎯 UTILISATEUR EXISTANT TROUVÉ!")
        print("SOLUTION 1: Mettre à jour l'utilisateur existant")
        print("SOLUTION 2: Supprimer et recréer")
        
        # Proposer la mise à jour
        return update_existing_user(existing_user['id'], user, admin_token)
    else:
        print(f"\n❓ Aucun utilisateur existant trouvé")
        print("Le conflit peut venir d'un autre problème")
        return False

def update_existing_user(keycloak_id, django_user, admin_token):
    """Mettre à jour l'utilisateur existant dans Keycloak"""
    
    print(f"\n🔄 Mise à jour utilisateur Keycloak ID: {keycloak_id}")
    
    headers = {
        'Authorization': f'Bearer {admin_token}',
        'Content-Type': 'application/json'
    }
    
    # Données à mettre à jour
    update_data = {
        'email': django_user.email,
        'username': django_user.email,  # Forcer username = email
        'firstName': django_user.prenom or 'Utilisateur',
        'lastName': django_user.nom or 'KeurDoctor',
        'enabled': django_user.est_actif,
        'emailVerified': True
    }
    
    try:
        update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{keycloak_id}"
        response = requests.put(update_url, json=update_data, headers=headers, timeout=10)
        
        if response.status_code == 204:  # No Content = Success
            print("✅ Utilisateur mis à jour avec succès!")
            return True
        else:
            print(f"❌ Erreur mise à jour: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de la mise à jour: {e}")
        return False

def main():
    print("🚀 DIAGNOSTIC ET RÉPARATION CONFLIT KEYCLOAK")
    print("=" * 60)
    
    problematic_email = "mouharassoulmd@gmail.com"
    
    success = fix_user_conflict(problematic_email)
    
    if success:
        print(f"\n✅ CONFLIT RÉSOLU!")
        print("Vous pouvez maintenant tester avec: python verify_user.py")
    else:
        print(f"\n❌ Conflit non résolu automatiquement")
        print("Intervention manuelle nécessaire dans Keycloak Admin Console")

if __name__ == "__main__":
    main()
