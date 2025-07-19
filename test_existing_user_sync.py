#!/usr/bin/env python
"""
Script pour tester la synchronisation d'un utilisateur existant
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.views import create_keycloak_user_with_role
import secrets
import string

def test_existing_user_sync():
    """Tester la synchronisation d'un utilisateur existant"""
    
    print("=== TEST SYNCHRONISATION UTILISATEUR EXISTANT ===")
    
    # Trouver un utilisateur existant
    try:
        utilisateur = Utilisateur.objects.filter(role_autorise__isnull=False).first()
        if not utilisateur:
            print("❌ Aucun utilisateur avec rôle trouvé dans la base de données")
            return
            
        print(f"Utilisateur trouvé: {utilisateur.email} (rôle: {utilisateur.role_autorise})")
        
        # Générer un nouveau mot de passe
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        print(f"Nouveau mot de passe généré: {new_password}")
        print("Tentative de synchronisation...")
        
        # Synchroniser avec Keycloak
        success = create_keycloak_user_with_role(utilisateur, utilisateur.role_autorise, new_password)
        
        if success:
            print("✅ Synchronisation réussie!")
            print(f"Email: {utilisateur.email}")
            print(f"Nouveau mot de passe: {new_password}")
            print(f"Rôle: {utilisateur.role_autorise}")
        else:
            print("❌ Échec de la synchronisation")
            
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_existing_user_sync() 