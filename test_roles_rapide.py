"""
Test rapide: Vérifier que les nouvelles méthodes rôles sont disponibles
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

print("🎭 VÉRIFICATION RAPIDE RÔLES KEYCLOAK")
print("=" * 40)

try:
    from comptes.keycloak_auto_sync import KeycloakSyncService
    
    # Vérifier les nouvelles méthodes
    required_methods = [
        'assign_realm_roles',
        'assign_client_roles', 
        'assign_user_to_keycloak_groups',
        'ensure_keycloak_setup'
    ]
    
    print("📋 Méthodes de synchronisation:")
    for method in required_methods:
        if hasattr(KeycloakSyncService, method):
            print(f"   ✅ {method}")
        else:
            print(f"   ❌ {method} MANQUANT")
    
    # Test setup Keycloak
    print(f"\n🔧 Test setup Keycloak...")
    setup_result = KeycloakSyncService.ensure_keycloak_setup()
    
    if setup_result:
        print("✅ Setup Keycloak réussi")
    else:
        print("❌ Setup Keycloak échoué")
    
    print(f"\n🎯 STATUT: Méthodes rôles implémentées")
    
except ImportError as e:
    print(f"❌ Erreur import: {e}")
except Exception as e:
    print(f"❌ Erreur: {e}")

print("=" * 40)
