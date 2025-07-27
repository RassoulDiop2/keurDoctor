#!/usr/bin/env python3
"""
Script pour appliquer les migrations en attente
"""
import os
import django
from django.core.management import execute_from_command_line

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

def main():
    print("🔧 Application des migrations en attente...")
    try:
        execute_from_command_line(['manage.py', 'showmigrations', 'comptes'])
        print("\n📋 Application de toutes les migrations...")
        execute_from_command_line(['manage.py', 'migrate'])
        print("✅ Migrations appliquées avec succès!")
    except Exception as e:
        print(f"❌ Erreur lors de l'application des migrations: {e}")

if __name__ == "__main__":
    main()
