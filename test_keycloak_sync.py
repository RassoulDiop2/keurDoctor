#!/usr/bin/env python
"""
Script de test pour vérifier la synchronisation Keycloak
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

logger = logging.getLogger(__name__)

def test_keycloak_sync():
    """Test de la synchronisation Keycloak"""
    
    print("=== TEST DE SYNCHRONISATION KEYCLOAK ===")
    
    # Récupérer un utilisateur de test
    try:
        test_user = Utilisateur.objects.filter(role_autorise__isnull=False).first()
        if not test_user:
            print("❌ Aucun utilisateur avec un rôle défini trouvé")
            return
            
        print(f"Utilisateur de test: {test_user.email} (rôle: {test_user.role_autorise})")
        
        # Test de synchronisation
        import secrets
        import string
        test_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        print(f"Tentative de synchronisation avec mot de passe: {test_password}")
        
        success = create_keycloak_user_with_role(test_user, test_user.role_autorise, test_password)
        
        if success:
            print("✅ Synchronisation réussie!")
        else:
            print("❌ Échec de la synchronisation")
            
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")

def check_keycloak_connection():
    """Vérifier la connexion à Keycloak"""
    
    print("\n=== VÉRIFICATION CONNEXION KEYCLOAK ===")
    
    try:
        from comptes.views import get_keycloak_admin_token
        from django.conf import settings
        
        print(f"URL Keycloak: {settings.KEYCLOAK_SERVER_URL}")
        print(f"Realm: {settings.OIDC_REALM}")
        
        token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
        
        if token:
            print("✅ Connexion à Keycloak réussie")
            print(f"Token obtenu: {token[:20]}...")
        else:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")

if __name__ == "__main__":
    check_keycloak_connection()
    test_keycloak_sync() 