#!/usr/bin/env python
"""
Script de diagnostic pour vérifier la base de données
"""
import os
import sys
import django
from pathlib import Path

# Configuration du chemin
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.db import connection
from django.conf import settings

def diagnostic_database():
    """Diagnostic complet de la base de données"""
    print("🔍 DIAGNOSTIC DE LA BASE DE DONNÉES")
    print("=" * 50)
    
    # Informations de connexion
    db_settings = settings.DATABASES['default']
    print(f"📊 Base de données: {db_settings['NAME']}")
    print(f"👤 Utilisateur: {db_settings['USER']}")
    print(f"🏠 Hôte: {db_settings['HOST']}")
    print(f"🔌 Port: {db_settings['PORT']}")
    print()
    
    try:
        with connection.cursor() as cursor:
            # Test de connexion
            print("✅ Connexion à la base de données réussie")
            
            # Vérifier la base actuelle
            cursor.execute("SELECT current_database();")
            current_db = cursor.fetchone()[0]
            print(f"📂 Base de données actuelle: {current_db}")
            
            # Vérifier le schéma actuel
            cursor.execute("SELECT current_schema();")
            current_schema = cursor.fetchone()[0]
            print(f"📁 Schéma actuel: {current_schema}")
            print()
            
            # Lister toutes les tables dans le schéma public
            print("📋 TABLES DANS LE SCHÉMA PUBLIC:")
            cursor.execute("""
                SELECT table_name, table_type 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            
            tables = cursor.fetchall()
            if tables:
                print(f"Trouvé {len(tables)} table(s):")
                for table_name, table_type in tables:
                    # Compter les enregistrements
                    try:
                        cursor.execute(f'SELECT COUNT(*) FROM "{table_name}";')
                        count = cursor.fetchone()[0]
                        print(f"  📊 {table_name} ({table_type}) - {count} enregistrement(s)")
                    except Exception as e:
                        print(f"  ❌ {table_name} ({table_type}) - Erreur: {e}")
            else:
                print("❌ Aucune table trouvée dans le schéma 'public'")
            
            print()
            
            # Vérifier les tables Django spécifiques
            print("🔍 VÉRIFICATION DES TABLES DJANGO:")
            django_tables = [
                'django_migrations',
                'comptes_utilisateur', 
                'comptes_medecin_new',
                'comptes_patient_new',
                'comptes_rendezvous',
                'comptes_consultation'
            ]
            
            for table in django_tables:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s;
                """, [table])
                
                exists = cursor.fetchone()[0]
                if exists:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table}";')
                    count = cursor.fetchone()[0]
                    print(f"  ✅ {table} - {count} enregistrement(s)")
                else:
                    print(f"  ❌ {table} - Table manquante")
            
            print()
            
            # Vérifier les migrations appliquées
            print("📝 MIGRATIONS APPLIQUÉES:")
            cursor.execute("""
                SELECT app, name, applied 
                FROM django_migrations 
                WHERE app = 'comptes'
                ORDER BY applied DESC;
            """)
            
            migrations = cursor.fetchall()
            if migrations:
                for app, name, applied in migrations:
                    print(f"  ✅ {app}.{name} - {applied}")
            else:
                print("  ❌ Aucune migration trouvée")
                
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        print()
        print("💡 SOLUTIONS POSSIBLES:")
        print("1. Vérifiez que PostgreSQL est démarré")
        print("2. Vérifiez que la base 'KeurDoctorBD' existe")
        print("3. Vérifiez les paramètres de connexion")
        print("4. Exécutez: python manage.py migrate --run-syncdb")

if __name__ == '__main__':
    diagnostic_database()
