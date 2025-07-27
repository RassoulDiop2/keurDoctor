#!/usr/bin/env python3
"""
Diagnostic des migrations Django - Version non bloquante
"""
import os
import sys
import subprocess
import time

def run_command_with_timeout(command, timeout=30):
    """Exécute une commande avec timeout"""
    try:
        print(f"🔧 Exécution: {' '.join(command)}")
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.stdout:
            print("📤 STDOUT:")
            print(result.stdout)
        if result.stderr:
            print("⚠️ STDERR:")
            print(result.stderr)
            
        return result.returncode == 0, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout après {timeout} secondes")
        return False, "", "Timeout"
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False, "", str(e)

def main():
    print("🔍 DIAGNOSTIC DES MIGRATIONS KEURDOCTOR")
    print("=" * 50)
    
    # Test 1: Vérifier la connexion à la base
    print("\n1️⃣ Test de connexion à la base de données...")
    success, stdout, stderr = run_command_with_timeout([
        'python.exe', 'manage.py', 'check', '--database', 'default'
    ], timeout=15)
    
    if not success:
        print("❌ Problème de connexion à la base de données")
        print("Vérifiez PostgreSQL et les paramètres dans settings.py")
        return
    
    # Test 2: État des migrations
    print("\n2️⃣ État des migrations comptes...")
    success, stdout, stderr = run_command_with_timeout([
        'python.exe', 'manage.py', 'showmigrations', 'comptes'
    ], timeout=10)
    
    if not success:
        print("❌ Impossible de vérifier les migrations")
        return
    
    # Test 3: Application des migrations
    print("\n3️⃣ Application des migrations...")
    success, stdout, stderr = run_command_with_timeout([
        'python.exe', 'manage.py', 'migrate', '--verbosity=2'
    ], timeout=60)
    
    if success:
        print("✅ Migrations appliquées avec succès!")
    else:
        print("❌ Échec de l'application des migrations")
        print("Essayez manuellement:")
        print("python.exe manage.py migrate --fake-initial")
    
    print("\n" + "=" * 50)
    print("🎯 DIAGNOSTIC TERMINÉ")
    
if __name__ == "__main__":
    main()
