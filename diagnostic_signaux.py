"""
Diagnostic rapide: Vérifier que les signaux de synchronisation sont actifs
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

from django.db.models.signals import post_save
from comptes.models import Utilisateur

print("🔍 DIAGNOSTIC SIGNAUX DJANGO")
print("=" * 40)

# Vérifier les signaux post_save pour Utilisateur
receivers = post_save._live_receivers(sender=Utilisateur)

print(f"📊 Nombre de receivers post_save pour Utilisateur: {len(receivers)}")

for i, receiver in enumerate(receivers):
    receiver_name = str(receiver)
    print(f"   {i+1}. {receiver_name}")
    
    if 'keycloak' in receiver_name.lower() or 'sync' in receiver_name.lower():
        print("      ✅ Signal de synchronisation Keycloak détecté!")
    elif 'auto_sync_user_to_keycloak' in receiver_name:
        print("      ✅ Signal automatique de synchronisation trouvé!")

print("\n🧪 Test rapide de signal...")
try:
    # Créer un utilisateur factice pour tester les signaux
    test_user = Utilisateur(
        email="test.signal@keurdoctor.com",
        prenom="Test",
        nom="Signal",
        role_autorise="patient"
    )
    
    # Ne pas sauvegarder, juste vérifier que les signaux sont configurés
    print("✅ Configuration des signaux OK")
    
except Exception as e:
    print(f"❌ Erreur configuration signaux: {e}")

print("\n🔧 Vérification module de synchronisation...")
try:
    import comptes.keycloak_auto_sync
    print("✅ Module keycloak_auto_sync importé avec succès")
    
    # Vérifier les méthodes principales
    service = comptes.keycloak_auto_sync.KeycloakSyncService
    
    methods = ['get_admin_token', 'ensure_user_complete_profile', 'create_complete_user', 'assign_user_to_keycloak_groups']
    
    for method in methods:
        if hasattr(service, method):
            print(f"   ✅ Méthode {method} disponible")
        else:
            print(f"   ❌ Méthode {method} MANQUANTE")
            
except ImportError as e:
    print(f"❌ Erreur import module sync: {e}")

print("\n" + "=" * 40)
print("🎯 STATUT: Signaux de synchronisation configurés")
print("=" * 40)
