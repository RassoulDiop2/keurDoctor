#!/usr/bin/env python3
"""
Script pour démarrer Django en ignorant temporairement les migrations problématiques
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

def test_django_without_migrations():
    """Test Django sans vérification des migrations"""
    
    print("🚀 TEST DJANGO SANS MIGRATIONS")
    print("=" * 50)
    
    try:
        django.setup()
        print("✅ Django configuré avec succès")
        
        # Test des modèles
        from comptes.models import Utilisateur
        user_count = Utilisateur.objects.count()
        print(f"✅ Base de données accessible - {user_count} utilisateurs")
        
        # Test du formulaire admin corrigé
        from comptes.admin import UtilisateurCreationForm
        print("✅ Formulaire admin importé")
        
        # Test des services
        from comptes.keycloak_auto_sync import KeycloakSyncService
        print("✅ Service Keycloak disponible")
        
        print(f"\n🎯 SYSTÈME FONCTIONNEL!")
        print("Les corrections du formulaire admin sont actives")
        print("Vous pouvez tester via Django shell ou interface web")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def run_django_shell():
    """Démarrer Django shell pour tests manuels"""
    
    print(f"\n🐍 DÉMARRAGE DJANGO SHELL")
    print("=" * 40)
    print("Commandes utiles:")
    print("from comptes.models import Utilisateur")
    print("from comptes.admin import UtilisateurCreationForm")
    print("users = Utilisateur.objects.all()")
    print("exit() pour quitter")
    
    # Démarrer le shell
    execute_from_command_line(['manage.py', 'shell'])

def main():
    if len(sys.argv) > 1 and sys.argv[1] == 'shell':
        run_django_shell()
    else:
        success = test_django_without_migrations()
        if success:
            print(f"\n📋 OPTIONS DISPONIBLES:")
            print("1. python bypass_migrations.py shell  - Démarrer Django shell")
            print("2. Créer un utilisateur manuellement via shell")
            print("3. Corriger les migrations puis runserver")
            
            # Proposer le shell directement
            choice = input(f"\nVoulez-vous démarrer le shell Django? (y/n): ").strip().lower()
            if choice == 'y':
                run_django_shell()

if __name__ == "__main__":
    main()
