#!/usr/bin/env python
"""
Script de test complet pour la synchronisation Keycloak
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.views import create_keycloak_user_with_role
import logging
import secrets
import string

logger = logging.getLogger(__name__)

def test_full_sync():
    """Test complet de la synchronisation"""
    
    print("=== TEST COMPLET DE SYNCHRONISATION KEYCLOAK ===")
    
    # Créer un utilisateur de test
    test_email = f"test.sync.{secrets.token_hex(4)}@keurdoctor.com"
    test_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
    
    print(f"Création d'un utilisateur de test: {test_email}")
    
    try:
        # Créer l'utilisateur dans Django
        user = Utilisateur.objects.create(
            email=test_email,
            prenom="Test",
            nom="Synchronisation",
            role_autorise="medecin",
            est_actif=True
        )
        
        print(f"✅ Utilisateur créé dans Django avec ID: {user.id}")
        
        # Synchroniser avec Keycloak
        print(f"Tentative de synchronisation avec Keycloak...")
        success = create_keycloak_user_with_role(user, user.role_autorise, test_password)
        
        if success:
            print("✅ Synchronisation réussie!")
            print(f"Email: {test_email}")
            print(f"Mot de passe: {test_password}")
            print(f"Rôle: {user.role_autorise}")
        else:
            print("❌ Échec de la synchronisation")
            
        # Nettoyer - supprimer l'utilisateur de test
        print("Nettoyage - suppression de l'utilisateur de test...")
        user.delete()
        print("✅ Utilisateur de test supprimé")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        
        # Nettoyer en cas d'erreur
        try:
            if 'user' in locals():
                user.delete()
                print("✅ Utilisateur de test supprimé après erreur")
        except:
            pass

def test_existing_user_sync():
    """Test de synchronisation d'un utilisateur existant"""
    
    print("\n=== TEST SYNCHRONISATION UTILISATEUR EXISTANT ===")
    
    try:
        # Récupérer un utilisateur existant
        existing_user = Utilisateur.objects.filter(role_autorise__isnull=False).first()
        if not existing_user:
            print("❌ Aucun utilisateur avec un rôle défini trouvé")
            return
            
        print(f"Utilisateur existant: {existing_user.email} (rôle: {existing_user.role_autorise})")
        
        # Générer un nouveau mot de passe
        new_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        print(f"Tentative de synchronisation avec nouveau mot de passe...")
        success = create_keycloak_user_with_role(existing_user, existing_user.role_autorise, new_password)
        
        if success:
            print("✅ Synchronisation réussie!")
            print(f"Email: {existing_user.email}")
            print(f"Nouveau mot de passe: {new_password}")
        else:
            print("❌ Échec de la synchronisation")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

if __name__ == "__main__":
    test_full_sync()
    test_existing_user_sync() 