#!/usr/bin/env python3
"""
🔄 RÉCUPÉRATION ET NETTOYAGE INTELLIGENT DU PROJET
Script pour récupérer les fichiers essentiels et nettoyer le projet
"""
import os
import shutil
import glob

print("🔄 RÉCUPÉRATION ET NETTOYAGE INTELLIGENT DU PROJET")
print("=" * 60)

def create_requirements_txt():
    """Crée le fichier requirements.txt avec les dépendances essentielles"""
    requirements_content = """Django==5.2.3
mozilla-django-oidc==4.0.1
psycopg2-binary==2.9.10
cryptography==45.0.4
django-axes==6.3.0
django-security==0.20.0
django-auditlog==2.4.0

# Dépendances HTTPS et sécurité avancée
django-sslserver==0.22
pyOpenSSL==23.3.0
django-redis==5.4.0
django-prometheus==2.3.1
gunicorn[gevent]==21.2.0

# Outils de sécurité et monitoring
requests[security]==2.31.0
python-dotenv==1.0.0
whitenoise==6.6.0

# Communication série pour RFID
pyserial==3.5
"""
    
    with open('requirements.txt', 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    print("✅ Créé: requirements.txt")

def create_start_bat():
    """Crée le fichier start.bat pour démarrer l'application"""
    start_bat_content = """@echo off
echo 🚀 DÉMARRAGE DE KEURDOCTOR
echo ============================

REM Activation de l'environnement virtuel
if exist "KDenv\\Scripts\\activate.bat" (
    echo ✅ Activation de l'environnement virtuel...
    call KDenv\\Scripts\\activate.bat
) else (
    echo ⚠️  Environnement virtuel non trouvé
)

REM Application des migrations
echo ✅ Application des migrations...
python manage.py migrate

REM Démarrage du serveur
echo ✅ Démarrage du serveur Django...
echo 🌐 Serveur disponible sur: http://127.0.0.1:8000
echo 📋 Interface admin: http://127.0.0.1:8000/admin
echo 🛑 Pour arrêter: Ctrl+C
echo.
python manage.py runserver 0.0.0.0:8000

pause
"""
    
    with open('start.bat', 'w', encoding='utf-8') as f:
        f.write(start_bat_content)
    print("✅ Créé: start.bat")

def preserve_debug_log():
    """Conserve ou crée le fichier debug.log"""
    debug_content = """# KeurDoctor - Fichier de logs
# Ce fichier contient les logs de l'application Django
# Les logs sont automatiquement générés lors de l'exécution

"""
    
    # Si le fichier existe déjà, on le conserve
    if not os.path.exists('debug.log'):
        with open('debug.log', 'w', encoding='utf-8') as f:
            f.write(debug_content)
        print("✅ Créé: debug.log")
    else:
        print("✅ Conservé: debug.log existant")

def get_files_to_delete():
    """Retourne la liste des fichiers à supprimer (SAUF les essentiels)"""
    files_to_delete = []
    
    # FICHIERS ESSENTIELS À CONSERVER ABSOLUMENT
    essential_files = {
        'manage.py',
        'requirements.txt',
        'urls.py',
        'db.sqlite3',
        'debug.log',
        'start.bat',
        'docker-compose.yml',
        'Dockerfile',
        '.gitattributes',
        'README.md',
        'AUTHENTIFICATION_RFID.md',
        'SYNCHRONISATION_KEYCLOAK.md',
        'start_local.sh',
        'stop.sh',
        'clean_project_intelligent.py'  # Ce script lui-même
    }
    
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
        
        # Fichiers batch et scripts (sauf start.bat)
        '*test*.bat',
        '*https*.bat',
        '*debug*.bat',
        '*.ps1',
        
        # Fichiers markdown de documentation temporaire
        'CORRECTION*.md',
        'MIGRATION*.md',
        'CONFIGURATION*.md',
        'GUIDE*.md',
        'RÉSUMÉ*.md',
        'SOLUTION*.md',
        'VALIDATION*.txt',
        'REMOVAL*.md',
        
        # Certificats SSL de test
        '*.pem',
        '*.key',
        '*.crt',
    ]
    
    # Recherche des fichiers à supprimer
    for pattern in patterns_to_delete:
        matches = glob.glob(pattern)
        for match in matches:
            if os.path.basename(match) not in essential_files:
                files_to_delete.append(match)
    
    return files_to_delete

def clean_files():
    """Supprime les fichiers inutiles"""
    print("\n🗑️  SUPPRESSION DES FICHIERS INUTILES")
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
            except Exception as e:
                print(f"❌ Erreur suppression {file_path}: {e}")
    
    print(f"\n📊 Total supprimé: {deleted_count} fichiers")

def clean_directories():
    """Supprime les dossiers inutiles"""
    print("\n🗂️  SUPPRESSION DES DOSSIERS INUTILES")
    print("-" * 40)
    
    dirs_to_delete = ['ssl']
    
    for dir_name in dirs_to_delete:
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
    
    pycache_count = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"✅ Supprimé: {pycache_path}")
                pycache_count += 1
            except Exception as e:
                print(f"❌ Erreur: {e}")
    
    print(f"📊 Total __pycache__ supprimés: {pycache_count}")

def clean_comptes_directory():
    """Nettoie le dossier comptes"""
    print("\n📁 NETTOYAGE DU DOSSIER COMPTES")
    print("-" * 40)
    
    comptes_files_to_keep = {
        '__init__.py',
        'admin.py',
        'apps.py',
        'auth_backends.py',
        'decorators.py',
        'forms.py',
        'keycloak_auto_sync.py',
        'middleware.py',
        'middleware_https.py',
        'models.py',
        'rfid_arduino_handler.py',
        'urls.py',
        'views.py',
        'views_rfid.py',
    }
    
    comptes_dir = 'comptes'
    if os.path.exists(comptes_dir):
        for file in os.listdir(comptes_dir):
            file_path = os.path.join(comptes_dir, file)
            if os.path.isfile(file_path) and file not in comptes_files_to_keep:
                if not file.endswith('.pyc') and not file.startswith('__'):
                    try:
                        os.remove(file_path)
                        print(f"✅ Supprimé: {file_path}")
                    except Exception as e:
                        print(f"❌ Erreur: {e}")

def show_final_structure():
    """Affiche la structure finale du projet"""
    print("\n📋 STRUCTURE FINALE DU PROJET")
    print("=" * 60)
    
    def print_directory_tree(directory, prefix="", max_depth=2, current_depth=0):
        if current_depth >= max_depth:
            return
            
        try:
            items = sorted([item for item in os.listdir(directory) if not item.startswith('.')])
            for i, item in enumerate(items):
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
    print("🚀 DÉBUT DU NETTOYAGE INTELLIGENT")
    
    # 1. Création/récupération des fichiers essentiels
    print("\n📦 CRÉATION DES FICHIERS ESSENTIELS")
    print("-" * 40)
    create_requirements_txt()
    create_start_bat()
    preserve_debug_log()
    
    # 2. Nettoyage des fichiers inutiles
    clean_files()
    
    # 3. Nettoyage des dossiers
    clean_directories()
    
    # 4. Nettoyage __pycache__
    clean_pycache()
    
    # 5. Nettoyage spécifique du dossier comptes
    clean_comptes_directory()
    
    print("\n" + "=" * 60)
    print("✅ NETTOYAGE INTELLIGENT TERMINÉ !")
    print("=" * 60)
    
    # Affichage de la structure finale
    show_final_structure()
    
    print("\n🎯 FICHIERS ESSENTIELS CONSERVÉS/CRÉÉS:")
    print("✅ requirements.txt - Dépendances Python")
    print("✅ debug.log - Fichier de logs")
    print("✅ start.bat - Script de démarrage")
    print("✅ manage.py - Commandes Django")
    print("✅ comptes/ - Application principale")
    print("✅ templates/ - Templates HTML")
    print("✅ static/ - Fichiers statiques")
    print("✅ keycloak-themes/ - Thèmes Keycloak")
    print("✅ KDenv/ - Environnement virtuel")
    
    print("\n🚀 COMMANDES POUR DÉMARRER:")
    print("1. Double-cliquez sur start.bat")
    print("   OU")
    print("2. python manage.py migrate && python manage.py runserver")
    
    print("\n🌐 URLs importantes:")
    print("- Application: http://127.0.0.1:8000")
    print("- Admin: http://127.0.0.1:8000/admin")
    print("- RFID: http://127.0.0.1:8000/rfid/")

if __name__ == "__main__":
    main()
