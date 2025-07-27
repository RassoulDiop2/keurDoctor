#!/usr/bin/env python3
"""
Script pour ajouter manuellement la colonne access_direct à la table comptes_rfidcard
"""
import os
import sys
import django

# Configuration Django
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

try:
    django.setup()
    from django.db import connection
    
    print("🔧 Ajout de la colonne access_direct à la table comptes_rfidcard...")
    
    with connection.cursor() as cursor:
        try:
            # Vérifier si la colonne existe déjà
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'comptes_rfidcard' 
                AND column_name = 'access_direct';
            """)
            
            if cursor.fetchone():
                print("✅ La colonne access_direct existe déjà!")
            else:
                # Ajouter la colonne
                cursor.execute("""
                    ALTER TABLE comptes_rfidcard 
                    ADD COLUMN access_direct BOOLEAN DEFAULT FALSE;
                """)
                
                print("✅ Colonne access_direct ajoutée avec succès!")
                
                # Enregistrer la migration dans la table django_migrations
                cursor.execute("""
                    INSERT INTO django_migrations (app, name, applied) 
                    VALUES ('comptes', '0010_add_access_direct_field', NOW())
                    ON CONFLICT DO NOTHING;
                """)
                
                print("✅ Migration enregistrée dans django_migrations")
            
            print("\n🎉 Correction terminée! Vous pouvez maintenant:")
            print("   1. Utiliser l'admin Django sans erreur")
            print("   2. Supprimer des utilisateurs avec des cartes RFID")
            print("   3. Le système RFID fonctionne avec les messages d'erreur améliorés")
            
        except Exception as e:
            print(f"❌ Erreur SQL: {e}")
            print("\n🔧 Solution alternative:")
            print("Exécutez manuellement cette commande SQL dans votre base de données:")
            print("ALTER TABLE comptes_rfidcard ADD COLUMN access_direct BOOLEAN DEFAULT FALSE;")
            
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    print("Assurez-vous d'être dans le bon répertoire et que Django est configuré.")
