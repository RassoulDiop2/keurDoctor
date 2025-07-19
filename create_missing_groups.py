#!/usr/bin/env python
"""
Script pour créer tous les groupes manquants dans Keycloak
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

def create_missing_groups():
    """Créer tous les groupes manquants dans Keycloak"""
    
    print("=== CRÉATION DES GROUPES MANQUANTS KEYCLOAK ===")
    
    try:
        admin_token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return
            
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Groupes à créer
        groups_to_create = [
            {
                'name': 'medecins',
                'description': 'Groupe pour les médecins'
            },
            {
                'name': 'patients', 
                'description': 'Groupe pour les patients'
            }
        ]
        
        group_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/groups"
        
        for group_data in groups_to_create:
            print(f"Tentative de création du groupe '{group_data['name']}'...")
            
            create_data = {
                "name": group_data['name'],
                "attributes": {
                    "description": [group_data['description']]
                }
            }
            
            response = requests.post(group_url, json=create_data, headers=headers)
            
            if response.status_code in (201, 409):  # 201 = créé, 409 = existe déjà
                print(f"✅ Groupe '{group_data['name']}' créé ou existe déjà")
            else:
                print(f"❌ Erreur lors de la création du groupe '{group_data['name']}': {response.status_code}")
                print(f"Réponse: {response.text}")
        
        # Vérifier tous les groupes
        print("\n=== VÉRIFICATION FINALE ===")
        group_resp = requests.get(group_url, headers=headers)
        
        if group_resp.status_code == 200:
            groups = group_resp.json()
            print(f"Groupes disponibles dans Keycloak ({len(groups)}):")
            
            for group in groups:
                print(f"  - '{group['name']}' (ID: {group['id']})")
                
            expected_groups = ['administrateurs', 'medecins', 'patients']
            print("\nGroupes attendus par l'application:")
            for expected in expected_groups:
                found = any(g['name'] == expected for g in groups)
                status = "✅" if found else "❌"
                print(f"  {status} '{expected}'")
                
        else:
            print(f"❌ Erreur lors de la récupération des groupes: {group_resp.status_code}")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    create_missing_groups() 