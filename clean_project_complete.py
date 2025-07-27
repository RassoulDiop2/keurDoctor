#!/usr/bin/env python3
"""
🧹 NETTOYAGE COMPLET DU PROJET KEURDOCTOR
Script pour supprimer tous les fichiers inutiles et organiser le projet
"""
import os
import shutil
import glob

print("🧹 NETTOYAGE COMPLET DU PROJET KEURDOCTOR")
print("=" * 60)

# FICHIERS À CONSERVER (essentiels au fonctionnement)
ESSENTIAL_FILES = {
    # Django Core
    'manage.py',
    'requirements.txt',
    'urls.py',
    'db.sqlite3',
    
    # Configuration
    'docker-compose.yml',
    'Dockerfile',
    '.gitattributes',
    
    # Documentation essentielle
    'README.md',
    'AUTHENTIFICATION_RFID.md',
    'SYNCHRONISATION_KEYCLOAK.md',
    
    # Scripts de production
    'start.bat',
    'start_local.sh',
    'stop.sh',
}

# DOSSIERS À CONSERVER
ESSENTIAL_DIRS = {
    'comptes',
    'keur_Doctor_app',
    'static',
    'templates',
    'keycloak-themes',
    '.git',
    'KDenv',
    '__pycache__',
    'migrations'
}

# FICHIERS DE TEST ET DEBUG À SUPPRIMER
def get_files_to_delete():
    """Retourne la liste des fichiers à supprimer"""
    files_to_delete = []
    
    # Patterns de fichiers à supprimer
    patterns_to_delete = [
        # Tests et diagnostics
        'test_*.py',
        'debug_*.py',
        'diagnostic_*.py',
        'validation_*.py',
        'verify_*.py',
        'check_*.py',
        'quick_*.py',
        
        # Scripts de réparation temporaires
        'fix_*.py',
        'repair_*.py',
        'create_test_*.py',
        'create_missing_*.py',
        'create_groups_*.py',
        'force_*.py',
        'bypass_*.py',
        'clean_*.py',  # Sauf ce script
        'apply_*.py',
        'run_*.py',
        'migrate_*.py',
        
        # Scripts spécifiques
        'advanced_409_resolver.py',
        'final_409_fix.py',
        'rfid_simulator.py',
        'https_proxy_server.py',
        'generate_ssl_certs.py',
        'settings_production_https.py',
        
        # Fichiers batch et scripts
        '*.bat',
        '*.ps1',
        '*.sh',
        
        # Logs
        '*.log',
        '*.txt',
        
        # Certificats SSL
        '*.pem',
        '*.key',
        '*.crt',
    ]
    
    # Recherche dans le répertoire racine du projet
    for pattern in patterns_to_delete:
        matches = glob.glob(pattern)
        for match in matches:
            # Ne pas supprimer ce script lui-même
            if match != 'clean_project_complete.py':
                files_to_delete.append(match)
    
    return files_to_delete

# DOSSIERS INUTILES À SUPPRIMER
DIRS_TO_DELETE = [
    'ssl',
    'management'  # Dans comptes/ si vide
]

def clean_files():
    """Supprime les fichiers inutiles"""
    print("🗑️  SUPPRESSION DES FICHIERS INUTILES")
    print("-" * 40)
    
    files_to_delete = get_files_to_delete()
    deleted_count = 0
    
    for file_path in files_to_delete:
        if os.path.exists(file_path):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"✅ Supprimé: {file_path}")
                    deleted_count += 1
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"✅ Dossier supprimé: {file_path}")
                    deleted_count += 1
            except Exception as e:
                print(f"❌ Erreur suppression {file_path}: {e}")
    
    print(f"\n📊 Total supprimé: {deleted_count} fichiers/dossiers")

def clean_directories():
    """Supprime les dossiers inutiles"""
    print("\n🗂️  SUPPRESSION DES DOSSIERS INUTILES")
    print("-" * 40)
    
    for dir_name in DIRS_TO_DELETE:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"✅ Dossier supprimé: {dir_name}")
            except Exception as e:
                print(f"❌ Erreur suppression {dir_name}: {e}")

def clean_pycache():
    """Supprime tous les __pycache__"""
    print("\n🐍 NETTOYAGE DES __pycache__")
    print("-" * 40)
    
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"✅ Supprimé: {pycache_path}")
            except Exception as e:
                print(f"❌ Erreur: {e}")

def clean_comptes_directory():
    """Nettoie le dossier comptes"""
    print("\n📁 NETTOYAGE DU DOSSIER COMPTES")
    print("-" * 40)
    
    comptes_files_to_keep = [
        '__init__.py',
        'admin.py',
        'apps.py',
        'auth_backends.py',
        'decorators.py',
        'forms.py',
        'keycloak_auto_sync.py',
        'middleware.py',
        'models.py',
        'rfid_arduino_handler.py',
        'urls.py',
        'views.py',
        'views_rfid.py',
    ]
    
    comptes_dir = 'comptes'
    if os.path.exists(comptes_dir):
        for file in os.listdir(comptes_dir):
            file_path = os.path.join(comptes_dir, file)
            if os.path.isfile(file_path) and file not in comptes_files_to_keep:
                if not file.endswith('.pyc'):
                    try:
                        os.remove(file_path)
                        print(f"✅ Supprimé: {file_path}")
                    except Exception as e:
                        print(f"❌ Erreur: {e}")

def show_final_structure():
    """Affiche la structure finale du projet"""
    print("\n📋 STRUCTURE FINALE DU PROJET")
    print("=" * 60)
    
    def print_directory_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
            
        try:
            items = sorted(os.listdir(directory))
            for i, item in enumerate(items):
                if item.startswith('.'):
                    continue
                    
                path = os.path.join(directory, item)
                is_last = i == len(items) - 1
                current_prefix = "└── " if is_last else "├── "
                print(f"{prefix}{current_prefix}{item}")
                
                if os.path.isdir(path) and current_depth < max_depth - 1:
                    extension = "    " if is_last else "│   "
                    print_directory_tree(path, prefix + extension, max_depth, current_depth + 1)
        except PermissionError:
            pass
    
    print_directory_tree(".")

def main():
    """Fonction principale"""
    print("🚀 DÉBUT DU NETTOYAGE")
    
    # Nettoyage des fichiers
    clean_files()
    
    # Nettoyage des dossiers
    clean_directories()
    
    # Nettoyage __pycache__
    clean_pycache()
    
    # Nettoyage spécifique du dossier comptes
    clean_comptes_directory()
    
    print("\n" + "=" * 60)
    print("✅ NETTOYAGE TERMINÉ !")
    print("=" * 60)
    
    # Affichage de la structure finale
    show_final_structure()
    
    print("\n🎯 FICHIERS CONSERVÉS (ESSENTIELS):")
    print("- manage.py (Django)")
    print("- requirements.txt (dépendances)")
    print("- comptes/ (application principale)")
    print("- templates/ (templates HTML)")
    print("- static/ (fichiers statiques)")
    print("- keycloak-themes/ (thèmes Keycloak)")
    print("- KDenv/ (environnement virtuel)")
    print("- README.md et docs essentielles")
    
    print("\n🗑️  FICHIERS SUPPRIMÉS:")
    print("- Tous les scripts de test (test_*.py)")
    print("- Scripts de debug (debug_*.py)")
    print("- Scripts de réparation temporaires (fix_*.py)")
    print("- Fichiers batch (.bat, .ps1, .sh)")
    print("- Logs et fichiers temporaires")
    print("- Certificats SSL de test")
    print("- __pycache__ et fichiers compilés")
    
    print("\n🚀 PROCHAINES ÉTAPES:")
    print("1. python manage.py migrate")
    print("2. python manage.py runserver")
    print("3. Tester l'application")

if __name__ == "__main__":
    main()
