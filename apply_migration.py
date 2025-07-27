import os
import django
import sys

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.core.management import execute_from_command_line

if __name__ == "__main__":
    print("🔧 Application de la migration pour corriger le champ access_direct...")
    try:
        execute_from_command_line(['manage.py', 'migrate', 'comptes'])
        print("✅ Migration appliquée avec succès!")
        print("Vous pouvez maintenant utiliser l'admin Django sans erreur.")
    except Exception as e:
        print(f"❌ Erreur lors de la migration: {e}")
        print("Veuillez exécuter manuellement: python manage.py migrate comptes")
