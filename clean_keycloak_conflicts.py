#!/usr/bin/env python
"""
Script pour nettoyer les conflits Keycloak et résoudre les problèmes de synchronisation
"""
import os
import sys
import django
import requests
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.views import get_keycloak_admin_token
import logging

logger = logging.getLogger(__name__)

def get_keycloak_users():
    """Récupérer tous les utilisateurs de Keycloak"""
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return []
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users"
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Erreur lors de la récupération des utilisateurs Keycloak: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return []

def delete_keycloak_user(user_id):
    """Supprimer un utilisateur de Keycloak"""
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
        response = requests.delete(url, headers=headers, timeout=10)
        
        return response.status_code in (204, 200)
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression: {e}")
        return False

def analyze_conflicts():
    """Analyser les conflits entre Django et Keycloak"""
    print("🔍 Analyse des conflits Django ↔ Keycloak...")
    
    # Récupérer les utilisateurs Django
    django_users = list(Utilisateur.objects.all())
    django_emails = {user.email for user in django_users}
    
    print(f"📊 Utilisateurs Django: {len(django_users)}")
    
    # Récupérer les utilisateurs Keycloak
    keycloak_users = get_keycloak_users()
    keycloak_emails = {user['email'] for user in keycloak_users if user.get('email')}
    
    print(f"📊 Utilisateurs Keycloak: {len(keycloak_users)}")
    
    # Analyser les différences
    only_in_keycloak = keycloak_emails - django_emails
    only_in_django = django_emails - keycloak_emails
    in_both = django_emails & keycloak_emails
    
    print(f"\n📈 Analyse:")
    print(f"  ✅ Dans les deux: {len(in_both)}")
    print(f"  ❌ Seulement dans Keycloak: {len(only_in_keycloak)}")
    print(f"  ❌ Seulement dans Django: {len(only_in_django)}")
    
    return {
        'django_users': django_users,
        'keycloak_users': keycloak_users,
        'only_in_keycloak': only_in_keycloak,
        'only_in_django': only_in_django,
        'in_both': in_both
    }

def clean_keycloak_orphans():
    """Nettoyer les utilisateurs orphelins dans Keycloak"""
    print("\n🧹 Nettoyage des utilisateurs orphelins dans Keycloak...")
    
    analysis = analyze_conflicts()
    
    if not analysis['only_in_keycloak']:
        print("✅ Aucun utilisateur orphelin à nettoyer")
        return
    
    print(f"🗑️ Suppression de {len(analysis['only_in_keycloak'])} utilisateurs orphelins...")
    
    deleted_count = 0
    for email in analysis['only_in_keycloak']:
        # Trouver l'utilisateur dans la liste Keycloak
        user_to_delete = None
        for user in analysis['keycloak_users']:
            if user.get('email') == email:
                user_to_delete = user
                break
        
        if user_to_delete:
            print(f"  🗑️ Suppression de {email}...")
            if delete_keycloak_user(user_to_delete['id']):
                print(f"    ✅ Supprimé")
                deleted_count += 1
            else:
                print(f"    ❌ Échec de suppression")
        else:
            print(f"  ⚠️ Utilisateur {email} introuvable dans la liste")
    
    print(f"\n📊 Résumé: {deleted_count}/{len(analysis['only_in_keycloak'])} utilisateurs supprimés")

def sync_missing_users():
    """Synchroniser les utilisateurs manquants dans Keycloak"""
    print("\n🔄 Synchronisation des utilisateurs manquants dans Keycloak...")
    
    analysis = analyze_conflicts()
    
    if not analysis['only_in_django']:
        print("✅ Aucun utilisateur à synchroniser")
        return
    
    print(f"🔄 Synchronisation de {len(analysis['only_in_django'])} utilisateurs...")
    
    from comptes.views import create_keycloak_user_with_role
    
    synced_count = 0
    for email in analysis['only_in_django']:
        user = Utilisateur.objects.get(email=email)
        print(f"  🔄 Synchronisation de {email} (rôle: {user.role_autorise})...")
        
        # Générer un mot de passe temporaire
        temp_password = f"TempPass{user.id}!"
        
        if create_keycloak_user_with_role(user, user.role_autorise or 'patient', temp_password):
            print(f"    ✅ Synchronisé")
            synced_count += 1
        else:
            print(f"    ❌ Échec de synchronisation")
    
    print(f"\n📊 Résumé: {synced_count}/{len(analysis['only_in_django'])} utilisateurs synchronisés")

def main():
    """Fonction principale"""
    print("🧹 Nettoyage des conflits Keycloak - KeurDoctor")
    print("=" * 50)
    
    # Vérifier la connexion Keycloak
    admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
    if not admin_token:
        print("❌ Impossible de se connecter à Keycloak")
        print("💡 Assurez-vous que Keycloak est démarré sur http://localhost:8080")
        return
    
    print("✅ Connexion Keycloak établie")
    
    # Analyser les conflits
    analysis = analyze_conflicts()
    
    if analysis['only_in_keycloak'] or analysis['only_in_django']:
        print(f"\n⚠️ Conflits détectés!")
        
        # Demander confirmation
        response = input("\nVoulez-vous nettoyer les conflits? (y/N): ").strip().lower()
        
        if response in ['y', 'yes', 'oui']:
            # Nettoyer les orphelins Keycloak
            clean_keycloak_orphans()
            
            # Synchroniser les utilisateurs manquants
            sync_missing_users()
            
            print("\n✅ Nettoyage terminé!")
        else:
            print("❌ Nettoyage annulé")
    else:
        print("\n✅ Aucun conflit détecté - synchronisation parfaite!")
    
    print("\n💡 Conseils:")
    print("  - Utilisez l'interface admin pour créer de nouveaux utilisateurs")
    print("  - Les utilisateurs seront automatiquement synchronisés avec Keycloak")
    print("  - Vérifiez les logs Django pour plus de détails")

if __name__ == "__main__":
    main() 