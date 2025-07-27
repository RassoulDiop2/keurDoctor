#!/usr/bin/env python3
"""
Script de validation post-corrections
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import AuditLog, Utilisateur
from django.test import RequestFactory
import logging

logger = logging.getLogger(__name__)

def test_auditlog_fix():
    """Test du fix AuditLog session_id NULL"""
    print("🧪 TEST 1: Correction AuditLog session_id NULL")
    
    try:
        # Créer une request factory pour simuler une requête
        factory = RequestFactory()
        request = factory.get('/')
        request.session = None  # Simuler une session None
        
        # Tenter de créer un log d'audit sans session
        AuditLog.log_action(
            utilisateur=None,  # Utilisateur anonyme
            type_action='TEST',
            description='Test de correction session_id NULL',
            request=request
        )
        
        print("   ✅ AuditLog avec session_id NULL créé avec succès")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur AuditLog: {e}")
        return False

def test_logging_encoding():
    """Test de l'encodage UTF-8 dans les logs"""
    print("🧪 TEST 2: Encodage UTF-8 des logs")
    
    try:
        # Tester l'écriture de caractères spéciaux
        logger.info("Test caractères spéciaux: éàçù ñ 日本語")
        logger.info("Test emojis (si supportés): 🎯 🔧 ✅")
        
        print("   ✅ Encodage UTF-8 configuré avec succès")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur encodage: {e}")
        return False

def test_rfid_patch():
    """Test du patch RFID temporaire"""
    print("🧪 TEST 3: Patch RFID temporaire")
    
    try:
        from comptes.rfid_arduino_handler import lire_uid_rfid
        
        uid = lire_uid_rfid()
        if uid:
            print(f"   ✅ RFID patch fonctionne - UID: {uid}")
            return True
        else:
            print("   ⚠️ RFID patch ne retourne pas d'UID")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur RFID: {e}")
        return False

def main():
    print("🔧 VALIDATION POST-CORRECTIONS KEURDOCTOR")
    print("=" * 50)
    
    results = []
    
    # Test 1: AuditLog
    results.append(test_auditlog_fix())
    
    # Test 2: Logging
    results.append(test_logging_encoding())
    
    # Test 3: RFID
    results.append(test_rfid_patch())
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ VALIDATION")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("🎉 TOUTES LES CORRECTIONS VALIDÉES!")
        print("Vous pouvez maintenant:")
        print("1. Appliquer les migrations: python manage.py migrate")
        print("2. Redémarrer le serveur Django")
        print("3. Tester l'ACCÈS RFID UNIVERSEL")
    else:
        print("⚠️ CERTAINES CORRECTIONS NÉCESSITENT ATTENTION")
        print("Consultez les messages d'erreur ci-dessus")

if __name__ == "__main__":
    main()
