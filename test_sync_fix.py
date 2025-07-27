#!/usr/bin/env python
"""
Script de test pour vérifier la synchronisation Keycloak après les corrections
"""
import os
import sys
import django
from django.conf import settings

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from django.contrib.auth.models import Group
from comptes.views import create_keycloak_user_with_role, get_keycloak_admin_token
import logging

logger = logging.getLogger(__name__)

def test_keycloak_connection():
    """Test de connexion à Keycloak"""
    print("🔍 Test de connexion à Keycloak...")
    
    token = get_keycloak_admin_token(settings.KEYCLOAK_SERVER_URL)
    if token:
        print("✅ Connexion Keycloak réussie")
        return True
    else:
        print("❌ Échec de connexion à Keycloak")
        return False

def test_user_creation_sync():
    """Test de création d'utilisateur avec synchronisation"""
    print("\n👤 Test de création d'utilisateur avec synchronisation...")
    
    # Créer un utilisateur de test
    test_email = f"test_sync_{int(time.time())}@keurdoctor.com"
    
    try:
        # Créer l'utilisateur dans Django
        user = Utilisateur.objects.create(
            email=test_email,
            prenom="Test",
            nom="Synchronisation",
            role_autorise="patient",
            is_active=True
        )
        
        print(f"✅ Utilisateur Django créé: {user.email}")
        
        # Tester la synchronisation Keycloak
        success = create_keycloak_user_with_role(user, "patient", "TestPassword123!")
        
        if success:
            print(f"✅ Synchronisation Keycloak réussie pour {user.email}")
        else:
            print(f"❌ Échec de synchronisation Keycloak pour {user.email}")
        
        # Nettoyer
        user.delete()
        print(f"🧹 Utilisateur de test supprimé: {test_email}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        return False

def check_existing_users():
    """Vérifier les utilisateurs existants"""
    print("\n📋 Vérification des utilisateurs existants...")
    
    users = Utilisateur.objects.all()
    print(f"Nombre d'utilisateurs Django: {users.count()}")
    
    for user in users[:5]:  # Afficher les 5 premiers
        print(f"  - {user.email} (rôle: {user.role_autorise})")
    
    if users.count() > 5:
        print(f"  ... et {users.count() - 5} autres")

def main():
    """Fonction principale de test"""
    print("🧪 Test de synchronisation Keycloak - KeurDoctor")
    print("=" * 50)
    
    # Test de connexion
    if not test_keycloak_connection():
        print("\n❌ Impossible de continuer sans connexion Keycloak")
        return
    
    # Vérifier les utilisateurs existants
    check_existing_users()
    
    # Test de création et synchronisation
    success = test_user_creation_sync()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Tous les tests sont passés avec succès!")
    else:
        print("⚠️ Certains tests ont échoué")
    
    print("\n💡 Conseils:")
    print("  - Vérifiez que Keycloak est démarré sur http://localhost:8080")
    print("  - Vérifiez les logs Django pour plus de détails")
    print("  - Utilisez l'interface admin pour créer des utilisateurs")

if __name__ == "__main__":
    import time
    main() 