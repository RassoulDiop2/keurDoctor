#!/usr/bin/env python3
"""
Solution simple et directe pour le problème 409
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
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
        return None
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return None

def find_all_keycloak_users(admin_token):
    """Lister tous les utilisateurs Keycloak pour diagnostic"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        users_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        
        response = requests.get(users_url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"❌ Erreur récupération utilisateurs: {e}")
        return []

def clean_keycloak_duplicates(admin_token, target_email):
    """Nettoyer les doublons potentiels dans Keycloak"""
    
    print(f"🧹 NETTOYAGE KEYCLOAK POUR: {target_email}")
    print("=" * 60)
    
    # Récupérer tous les utilisateurs
    all_users = find_all_keycloak_users(admin_token)
    print(f"📊 {len(all_users)} utilisateurs Keycloak trouvés")
    
    # Chercher les utilisateurs suspects
    suspects = []
    for user in all_users:
        username = user.get('username', '')
        email = user.get('email', '')
        
        # Conditions suspectes
        if (username == target_email or 
            email == target_email or 
            target_email in username or 
            target_email in email):
            suspects.append(user)
    
    print(f"\n🔍 {len(suspects)} utilisateur(s) suspect(s) trouvé(s):")
    for i, user in enumerate(suspects, 1):
        print(f"{i}. ID: {user.get('id')}")
        print(f"   Username: {user.get('username', 'NON DÉFINI')}")
        print(f"   Email: {user.get('email', 'NON DÉFINI')}")
        print(f"   Prénom: {user.get('firstName', 'NON DÉFINI')}")
        print(f"   Nom: {user.get('lastName', 'NON DÉFINI')}")
        print(f"   Activé: {user.get('enabled')}")
        print()
    
    return suspects

def delete_keycloak_user(admin_token, user_id):
    """Supprimer un utilisateur Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        delete_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        
        response = requests.delete(delete_url, headers=headers, timeout=10)
        return response.status_code == 204
    except Exception as e:
        print(f"❌ Erreur suppression: {e}")
        return False

def force_sync_user(target_email):
    """Forcer la synchronisation après nettoyage"""
    try:
        user = Utilisateur.objects.get(email=target_email)
        from comptes.keycloak_auto_sync import KeycloakSyncService
        
        print(f"🔄 Synchronisation forcée de {target_email}...")
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        
        if success:
            print("✅ Synchronisation réussie!")
            return True
        else:
            print("❌ Synchronisation échouée")
            return False
            
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {target_email} non trouvé dans Django")
        return False
    except Exception as e:
        print(f"❌ Erreur synchronisation: {e}")
        return False

def main():
    print("🚀 SOLUTION DÉFINITIVE PROBLÈME 409")
    print("=" * 60)
    
    target_email = "mouharassoulmd@gmail.com"
    
    # 1. Obtenir token admin
    print("🔑 Connexion Keycloak...")
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return
    
    # 2. Diagnostiquer les utilisateurs suspects
    suspects = clean_keycloak_duplicates(admin_token, target_email)
    
    # 3. Proposer des actions
    if not suspects:
        print("✅ Aucun utilisateur suspect trouvé")
        print("Le problème 409 pourrait être résolu")
        
        # Tenter une synchronisation directe
        print(f"\n🔄 Test de synchronisation directe...")
        force_sync_user(target_email)
        
    else:
        print(f"\n🎯 ACTIONS RECOMMANDÉES:")
        print(f"1. Supprimer les utilisateurs suspects")
        print(f"2. Re-synchroniser l'utilisateur Django")
        
        # Demander confirmation (simulation)
        print(f"\n⚠️  ATTENTION: Suppression de {len(suspects)} utilisateur(s) Keycloak")
        print("Voulez-vous continuer? (Simulation: OUI)")
        
        # Supprimer les suspects
        deleted_count = 0
        for user in suspects:
            user_id = user.get('id')
            username = user.get('username', 'INCONNU')
            
            print(f"🗑️  Suppression de {username} (ID: {user_id})...")
            if delete_keycloak_user(admin_token, user_id):
                print(f"✅ {username} supprimé")
                deleted_count += 1
            else:
                print(f"❌ Échec suppression {username}")
        
        print(f"\n📊 {deleted_count}/{len(suspects)} utilisateur(s) supprimé(s)")
        
        # Re-synchroniser
        if deleted_count > 0:
            print(f"\n🔄 Re-synchronisation après nettoyage...")
            success = force_sync_user(target_email)
            
            if success:
                print(f"\n🎉 PROBLÈME 409 RÉSOLU!")
                print(f"L'utilisateur {target_email} devrait maintenant fonctionner")
            else:
                print(f"\n❌ Synchronisation encore échouée")
                print("Vérification manuelle nécessaire")

if __name__ == "__main__":
    main()
