"""
Test ultra-simple: Vérifier que les signaux fonctionnent
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

from django.db.models.signals import post_save
from comptes.models import Utilisateur

print("Signaux post_save pour Utilisateur:")
receivers = post_save._live_receivers(sender=Utilisateur)
print(f"Nombre: {len(receivers)}")

for receiver in receivers:
    name = str(receiver)
    if 'keycloak' in name.lower() or 'sync' in name.lower():
        print("✅ Signal sync trouvé")
        break
else:
    print("❌ Aucun signal sync")

try:
    import comptes.keycloak_auto_sync
    service = comptes.keycloak_auto_sync.KeycloakSyncService
    if hasattr(service, 'assign_user_to_keycloak_groups'):
        print("✅ Méthode groupes OK")
    else:
        print("❌ Méthode groupes manquante")
except:
    print("❌ Module sync non trouvé")

print("Test terminé")
