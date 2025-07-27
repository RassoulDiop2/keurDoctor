#!/usr/bin/env python3
"""
Script pour réinitialiser les migrations AuditLog problématiques
"""
import os
import glob
import shutil

def reset_auditlog_migrations():
    """Réinitialiser les migrations AuditLog"""
    
    print("🔧 RÉINITIALISATION MIGRATIONS AUDITLOG")
    print("=" * 60)
    
    migrations_dir = "comptes/migrations"
    
    # 1. Sauvegarder les migrations actuelles
    backup_dir = "migrations_backup"
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"📁 Dossier de sauvegarde créé: {backup_dir}")
    
    # 2. Identifier les migrations problématiques
    problematic_patterns = [
        "*fix_auditlog*",
        "*merge*"
    ]
    
    problematic_files = []
    for pattern in problematic_patterns:
        files = glob.glob(f"{migrations_dir}/{pattern}")
        problematic_files.extend(files)
    
    print(f"🗑️  Migrations problématiques trouvées:")
    for f in problematic_files:
        filename = os.path.basename(f)
        print(f"   - {filename}")
        
        # Sauvegarder avant suppression
        backup_path = os.path.join(backup_dir, filename)
        shutil.copy2(f, backup_path)
        print(f"     ✅ Sauvegardé vers {backup_path}")
    
    # 3. Supprimer les migrations problématiques
    print(f"\n🗑️  Suppression des migrations problématiques:")
    for f in problematic_files:
        try:
            os.remove(f)
            filename = os.path.basename(f)
            print(f"✅ Supprimé: {filename}")
        except Exception as e:
            print(f"❌ Erreur suppression {f}: {e}")
    
    # 4. Lister les migrations restantes
    print(f"\n📋 Migrations restantes:")
    remaining_migrations = sorted(glob.glob(f"{migrations_dir}/00*.py"))
    for f in remaining_migrations:
        filename = os.path.basename(f)
        print(f"   - {filename}")
    
    print(f"\n✅ RÉINITIALISATION TERMINÉE!")
    
    return len(problematic_files) > 0

def create_simple_auditlog_migration():
    """Créer une migration simple pour AuditLog si nécessaire"""
    
    migration_content = '''# Generated migration for AuditLog session_id fix

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('comptes', '0010_add_access_direct_field'),  # Dernière migration stable
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='session_id',
            field=models.CharField(max_length=100, blank=True, null=True, 
                                   help_text='ID de session (peut être vide pour utilisateurs anonymes)'),
        ),
    ]
'''
    
    migration_file = "comptes/migrations/0011_simple_auditlog_fix.py"
    with open(migration_file, 'w', encoding='utf-8') as f:
        f.write(migration_content)
    
    print(f"✅ Migration simple créée: {migration_file}")

def main():
    print("🚀 RÉPARATEUR DE MIGRATIONS")
    print("=" * 60)
    
    # Réinitialiser les migrations problématiques
    had_problems = reset_auditlog_migrations()
    
    if had_problems:
        print(f"\n🔧 Création d'une migration simple de remplacement...")
        create_simple_auditlog_migration()
    
    print(f"\n🎯 PROCHAINES ÉTAPES:")
    print("1. python manage.py migrate")
    print("2. python manage.py runserver")
    print("3. Tester la création d'utilisateur via interface admin")
    
    print(f"\n📁 Sauvegrades disponibles dans: migrations_backup/")

if __name__ == "__main__":
    main()
