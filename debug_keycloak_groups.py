#!/usr/bin/env python
"""
Script pour déboguer les groupes Keycloak
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.views import get_keycloak_admin_token
from django.conf import settings
import requests
import json

def debug_keycloak_groups():
    """Déboguer les groupes Keycloak"""
    
    print("=== DÉBOGUAGE GROUPES KEYCLOAK ===")
    
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return
            
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Récupérer tous les groupes
        group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
        group_resp = requests.get(group_url, headers=headers)
        
        if group_resp.status_code == 200:
            groups = group_resp.json()
            print(f"✅ {len(groups)} groupes trouvés dans Keycloak:")
            
            for group in groups:
                print(f"  - ID: {group['id']}")
                print(f"    Nom: '{group['name']}'")
                print(f"    Path: {group.get('path', 'N/A')}")
                print()
                
            # Vérifier les groupes attendus
            expected_groups = ['administrateurs', 'medecins', 'patients']
            print("Groupes attendus par l'application:")
            for expected in expected_groups:
                found = any(g['name'] == expected for g in groups)
                status = "✅" if found else "❌"
                print(f"  {status} '{expected}'")
                
        else:
            print(f"❌ Erreur lors de la récupération des groupes: {group_resp.status_code}")
            print(f"Réponse: {group_resp.text}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

def debug_user_groups(email):
    """Déboguer les groupes d'un utilisateur spécifique"""
    
    print(f"\n=== GROUPES DE L'UTILISATEUR {email} ===")
    
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return
            
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Chercher l'utilisateur
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}"
        search_resp = requests.get(search_url, headers=headers)
        
        if search_resp.status_code == 200 and search_resp.json():
            user_id = search_resp.json()[0]['id']
            print(f"✅ Utilisateur trouvé avec ID: {user_id}")
            
            # Récupérer les groupes de l'utilisateur
            user_groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups"
            user_groups_resp = requests.get(user_groups_url, headers=headers)
            
            if user_groups_resp.status_code == 200:
                user_groups = user_groups_resp.json()
                print(f"Groupes de l'utilisateur ({len(user_groups)}):")
                
                for group in user_groups:
                    print(f"  - {group['name']} (ID: {group['id']})")
                    
                if not user_groups:
                    print("  ❌ Aucun groupe attribué")
            else:
                print(f"❌ Erreur lors de la récupération des groupes: {user_groups_resp.status_code}")
        else:
            print(f"❌ Utilisateur {email} non trouvé dans Keycloak")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    debug_keycloak_groups()
    debug_user_groups("moustaf@keurdoctor.com") 