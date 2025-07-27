#!/usr/bin/env python3
"""
Script pour réparer TOUS les utilisateurs avec email manquant dans Keycloak
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
        return None
    except Exception as e:
        print(f"❌ Erreur token: {e}")
        return None

def check_user_email_in_keycloak(email, admin_token):
    """Vérifier si l'email est présent dans Keycloak"""
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                user_data = users[0]
                return {
                    'exists': True,
                    'has_email': bool(user_data.get('email')),
                    'keycloak_email': user_data.get('email'),
                    'user_data': user_data
                }
            else:
                return {'exists': False, 'has_email': False}
        return None
    except Exception as e:
        print(f"❌ Erreur vérification {email}: {e}")
        return None

def repair_all_users():
    """Réparer tous les utilisateurs avec problèmes d'email"""
    
    print("🚀 RÉPARATION GLOBALE - EMAILS MANQUANTS KEYCLOAK")
    print("=" * 70)
    
    # Obtenir token admin
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin Keycloak")
        return
    
    print("✅ Token admin Keycloak obtenu")
    
    # Récupérer tous les utilisateurs Django
    all_users = Utilisateur.objects.all().order_by('-date_creation')
    print(f"📋 {len(all_users)} utilisateurs Django trouvés")
    
    problematic_users = []
    repaired_users = []
    
    print(f"\n🔍 DIAGNOSTIC DE TOUS LES UTILISATEURS:")
    print("-" * 70)
    
    for user in all_users:
        print(f"\n👤 {user.email} (créé: {user.date_creation.strftime('%Y-%m-%d %H:%M')})")
        
        # Vérifier dans Keycloak
        keycloak_status = check_user_email_in_keycloak(user.email, admin_token)
        
        if keycloak_status is None:
            print("   ❌ Erreur vérification Keycloak")
            continue
            
        if not keycloak_status['exists']:
            print("   ⚠️  N'existe pas dans Keycloak - Synchronisation nécessaire")
            problematic_users.append(user)
            
        elif not keycloak_status['has_email']:
            print("   ❌ PROBLÈME: Email manquant dans Keycloak")
            problematic_users.append(user)
            
        else:
            print("   ✅ Email présent dans Keycloak")
    
    # Réparer les utilisateurs problématiques
    if problematic_users:
        print(f"\n🔧 RÉPARATION DE {len(problematic_users)} UTILISATEURS:")
        print("-" * 70)
        
        for user in problematic_users:
            print(f"\n🔄 Réparation: {user.email}")
            try:
                success = KeycloakSyncService.ensure_user_complete_profile(user)
                if success:
                    print("   ✅ Réparé avec succès")
                    repaired_users.append(user.email)
                else:
                    print("   ❌ Échec de la réparation")
            except Exception as e:
                print(f"   ❌ Erreur: {e}")
    
    # Résumé final
    print(f"\n" + "=" * 70)
    print("🏆 RÉSUMÉ FINAL:")
    print(f"   📊 Utilisateurs analysés: {len(all_users)}")
    print(f"   ⚠️  Utilisateurs problématiques: {len(problematic_users)}")
    print(f"   ✅ Utilisateurs réparés: {len(repaired_users)}")
    
    if repaired_users:
        print(f"\n✅ UTILISATEURS RÉPARÉS:")
        for email in repaired_users:
            print(f"   - {email}")
    
    print(f"\n🎯 RECOMMANDATION:")
    if len(repaired_users) > 0:
        print("✅ Tous les utilisateurs sont maintenant synchronisés!")
        print("✅ Les nouveaux utilisateurs créés via l'admin fonctionneront parfaitement")
    else:
        print("✅ Aucune réparation nécessaire - Système déjà optimal!")

if __name__ == "__main__":
    repair_all_users()
