#!/usr/bin/env python
"""
Script pour vérifier la structure de la table RFIDCard et réparer la base de données
"""
import os
import django
import sys

# Ajouter le répertoire du projet au PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__))))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.db import connection
from django.core.management import execute_from_command_line
from comptes.models import RFIDCard

def check_table_structure():
    """Vérifier la structure de la table comptes_rfidcard"""
    with connection.cursor() as cursor:
        try:
            # Obtenir la structure de la table
            cursor.execute("""
                SELECT column_name, data_type, is_nullable, column_default 
                FROM information_schema.columns 
                WHERE table_name = 'comptes_rfidcard' 
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("=== Structure actuelle de la table comptes_rfidcard ===")
            for col in columns:
                print(f"- {col[0]} ({col[1]}) - Nullable: {col[2]}, Default: {col[3]}")
            
            print("\n=== Champs requis par le modèle Django ===")
            for field in RFIDCard._meta.fields:
                print(f"- {field.name} ({field.__class__.__name__})")
            
            # Vérifier si access_direct existe
            column_names = [col[0] for col in columns]
            if 'access_direct' not in column_names:
                print("\n❌ PROBLÈME: La colonne 'access_direct' n'existe pas dans la base de données!")
                print("🔧 Solution: Ajouter la colonne manuellement")
                return False
            else:
                print("\n✅ La colonne 'access_direct' existe dans la base de données")
                return True
                
        except Exception as e:
            print(f"Erreur lors de la vérification: {e}")
            return False

def add_missing_column():
    """Ajouter la colonne access_direct si elle n'existe pas"""
    with connection.cursor() as cursor:
        try:
            print("🔧 Ajout de la colonne access_direct...")
            cursor.execute("""
                ALTER TABLE comptes_rfidcard 
                ADD COLUMN access_direct BOOLEAN DEFAULT FALSE;
            """)
            print("✅ Colonne access_direct ajoutée avec succès!")
            
            # Mettre à jour la description de la colonne
            cursor.execute("""
                COMMENT ON COLUMN comptes_rfidcard.access_direct 
                IS 'Permet l''accès direct au dashboard sans OTP';
            """)
            print("✅ Commentaire ajouté à la colonne")
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout de la colonne: {e}")
            return False

if __name__ == "__main__":
    print("=== Diagnostic de la table RFIDCard ===\n")
    
    # Vérifier la structure
    structure_ok = check_table_structure()
    
    if not structure_ok:
        print("\n=== Tentative de réparation ===")
        if add_missing_column():
            print("\n🎉 Base de données réparée avec succès!")
            print("Vous pouvez maintenant utiliser l'admin Django sans erreur.")
        else:
            print("\n❌ Échec de la réparation automatique")
            print("Veuillez exécuter manuellement:")
            print("ALTER TABLE comptes_rfidcard ADD COLUMN access_direct BOOLEAN DEFAULT FALSE;")
    else:
        print("\n✅ La base de données est correcte!")
