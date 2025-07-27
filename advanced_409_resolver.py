#!/usr/bin/env python3
"""
Script avancé pour résoudre les conflits Keycloak 409
"""
import os
import django
import requests
import json

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from django.conf import settings

def get_admin_token():
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
        return None
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return None

def search_all_keycloak_users(admin_token):
    """Récupérer TOUS les utilisateurs Keycloak pour analyse"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Erreur récupération utilisateurs: {e}")
        return []

def find_problematic_user(email, all_users):
    """Trouver l'utilisateur problématique par différents critères"""
    
    print(f"🔍 RECHERCHE APPROFONDIE DE: {email}")
    print("=" * 60)
    
    candidates = []
    
    # Recherche par email exact
    for user in all_users:
        if user.get('email') == email:
            candidates.append(('email_exact', user))
    
    # Recherche par username exact
    for user in all_users:
        if user.get('username') == email:
            candidates.append(('username_exact', user))
    
    # Recherche par email vide mais username similaire
    email_prefix = email.split('@')[0]
    for user in all_users:
        if (not user.get('email') or user.get('email') == '') and email_prefix in user.get('username', ''):
            candidates.append(('username_partial', user))
    
    # Recherche par firstName/lastName
    for user in all_users:
        first_name = user.get('firstName', '').lower()
        last_name = user.get('lastName', '').lower()
        if 'rassoul' in first_name.lower() or 'diop' in last_name.lower():
            candidates.append(('name_match', user))
    
    return candidates

def delete_keycloak_user(user_id, admin_token):
    """Supprimer un utilisateur Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        response = requests.delete(url, headers=headers, timeout=10)
        return response.status_code == 204
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        return False

def update_keycloak_user(user_id, user_data, admin_token):
    """Mettre à jour un utilisateur Keycloak"""
    try:
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        response = requests.put(url, headers=headers, json=user_data, timeout=10)
        return response.status_code == 204
    except Exception as e:
        print(f"❌ Erreur mise à jour: {e}")
        return False

def force_create_user(email, admin_token):
    """Forcer la création après nettoyage"""
    try:
        from comptes.keycloak_auto_sync import KeycloakSyncService
        user = Utilisateur.objects.get(email=email)
        return KeycloakSyncService.ensure_user_complete_profile(user)
    except Exception as e:
        print(f"❌ Erreur création forcée: {e}")
        return False

def resolve_409_conflict(email):
    """Résoudre le conflit 409 de manière définitive"""
    
    print(f"🚀 RÉSOLUTION DÉFINITIVE CONFLIT 409")
    print("=" * 60)
    print(f"🎯 Utilisateur problématique: {email}")
    
    # 1. Obtenir token admin
    admin_token = get_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return False
    
    # 2. Récupérer tous les utilisateurs Keycloak
    print(f"\n📋 Récupération de tous les utilisateurs Keycloak...")
    all_users = search_all_keycloak_users(admin_token)
    print(f"✅ {len(all_users)} utilisateurs récupérés")
    
    # 3. Trouver les candidats problématiques
    candidates = find_problematic_user(email, all_users)
    
    if not candidates:
        print(f"⚠️  Aucun candidat trouvé - Conflit mystérieux")
        return False
    
    print(f"\n🔍 CANDIDATS TROUVÉS:")
    for i, (match_type, user) in enumerate(candidates, 1):
        print(f"\n{i}. Type: {match_type}")
        print(f"   ID: {user.get('id')}")
        print(f"   Username: {user.get('username')}")
        print(f"   Email: {user.get('email', 'NON DÉFINI')}")
        print(f"   Prénom: {user.get('firstName', 'NON DÉFINI')}")
        print(f"   Nom: {user.get('lastName', 'NON DÉFINI')}")
        print(f"   Activé: {user.get('enabled')}")
    
    # 4. Stratégie de résolution
    print(f"\n🔧 STRATÉGIES DE RÉSOLUTION:")
    print("1. Supprimer tous les candidats et recréer")
    print("2. Mettre à jour le meilleur candidat")
    print("3. Analyse manuelle")
    
    # Stratégie automatique : supprimer et recréer
    print(f"\n🎯 STRATÉGIE CHOISIE: Suppression et recréation")
    
    deleted_count = 0
    for match_type, user in candidates:
        user_id = user.get('id')
        username = user.get('username')
        
        print(f"\n🗑️  Suppression utilisateur {username} (ID: {user_id})")
        if delete_keycloak_user(user_id, admin_token):
            print(f"✅ Utilisateur {username} supprimé")
            deleted_count += 1
        else:
            print(f"❌ Échec suppression {username}")
    
    if deleted_count > 0:
        print(f"\n✅ {deleted_count} utilisateur(s) supprimé(s)")
        
        # 5. Recréer l'utilisateur proprement
        print(f"\n🔄 Recréation de l'utilisateur {email}...")
        if force_create_user(email, admin_token):
            print(f"✅ UTILISATEUR RECRÉÉ AVEC SUCCÈS!")
            return True
        else:
            print(f"❌ Échec de la recréation")
            return False
    else:
        print(f"❌ Aucun utilisateur supprimé - Conflit persistant")
        return False

def main():
    print("🚀 RÉSOLVEUR AVANCÉ DE CONFLITS 409")
    print("=" * 60)
    
    # Utilisateur problématique identifié
    problematic_email = "mouharassoulmd@gmail.com"
    
    success = resolve_409_conflict(problematic_email)
    
    if success:
        print(f"\n🎉 CONFLIT RÉSOLU AVEC SUCCÈS!")
        print(f"L'utilisateur {problematic_email} peut maintenant se connecter")
        print(f"\n🔍 Vérification recommandée:")
        print(f"python verify_user.py")
    else:
        print(f"\n❌ ÉCHEC DE LA RÉSOLUTION")
        print(f"Vérification manuelle nécessaire dans l'interface Keycloak")

if __name__ == "__main__":
    main()
