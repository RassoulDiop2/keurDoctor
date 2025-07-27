#!/usr/bin/env python3
"""
Script pour nettoyer et réparer les migrations problématiques
"""
import os
import glob

print("🔧 NETTOYAGE DES MIGRATIONS PROBLÉMATIQUES")
print("=" * 60)

# Répertoire des migrations
migrations_dir = "comptes/migrations"

# Lister toutes les migrations
print("📋 Migrations actuelles:")
migration_files = sorted(glob.glob(f"{migrations_dir}/00*.py"))
for f in migration_files:
    filename = os.path.basename(f)
    print(f"   - {filename}")

# Migrations problématiques à supprimer
problematic_migrations = [
    "0002_fix_auditlog_session_id.py",
    "0012_merge_20250726_1920.py"
]

print(f"\n🗑️  Suppression des migrations problématiques:")
for migration in problematic_migrations:
    migration_path = f"{migrations_dir}/{migration}"
    if os.path.exists(migration_path):
        try:
            os.remove(migration_path)
            print(f"✅ Supprimé: {migration}")
        except Exception as e:
            print(f"❌ Erreur suppression {migration}: {e}")
    else:
        print(f"⚠️  Déjà supprimé: {migration}")

print(f"\n📋 Migrations restantes après nettoyage:")
remaining_files = sorted(glob.glob(f"{migrations_dir}/00*.py"))
for f in remaining_files:
    filename = os.path.basename(f)
    print(f"   - {filename}")

print(f"\n✅ Nettoyage terminé!")
print(f"\n🎯 PROCHAINES ÉTAPES:")
print("1. Essayez: python manage.py migrate")
print("2. Si erreur: python manage.py makemigrations comptes")
print("3. Puis: python manage.py migrate")
print("4. Enfin: python manage.py runserver")
