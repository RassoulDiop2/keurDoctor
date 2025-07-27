#!/usr/bin/env python3
"""
Script simple pour appliquer les migrations Django
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

# Configuration de l'environnement Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

def main():
    """Applique les migrations Django"""
    try:
        print("🔧 Configuration Django...")
        django.setup()
        
        print("📋 Vérification des migrations en attente...")
        execute_from_command_line(['manage.py', 'showmigrations', 'comptes'])
        
        print("\n🚀 Application des migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        
        print("✅ Migrations appliquées avec succès!")
        print("\n🎯 PROCHAINES ÉTAPES:")
        print("1. Redémarrer le serveur Django")
        print("2. Tester l'ACCÈS RFID UNIVERSEL")
        print("3. Vérifier les logs pour absence d'erreurs")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'application des migrations: {e}")
        print("\n🔍 SOLUTION ALTERNATIVE:")
        print("Exécutez manuellement dans le terminal:")
        print("python.exe manage.py migrate")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
