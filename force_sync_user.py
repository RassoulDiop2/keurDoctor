#!/usr/bin/env python3
"""
Script pour forcer la synchronisation d'un utilisateur spécifique
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.keycloak_auto_sync import KeycloakSyncService

def force_sync_user(email):
    """Forcer la synchronisation d'un utilisateur vers Keycloak"""
    
    print(f"🔧 SYNCHRONISATION FORCÉE: {email}")
    print("=" * 60)
    
    try:
        # Récupérer l'utilisateur
        user = Utilisateur.objects.get(email=email)
        print(f"✅ Utilisateur Django trouvé:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
        
        # Forcer la synchronisation
        print(f"\n🔄 Forçage de la synchronisation Keycloak...")
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        
        if success:
            print("✅ SYNCHRONISATION RÉUSSIE!")
            print("L'utilisateur devrait maintenant être présent dans Keycloak")
        else:
            print("❌ ÉCHEC DE LA SYNCHRONISATION")
            print("Vérifiez les logs pour plus de détails")
            
        return success
        
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {email} non trouvé dans Django")
        return False
    except Exception as e:
        print(f"❌ Erreur lors de la synchronisation: {e}")
        return False

def main():
    print("🚀 OUTIL DE SYNCHRONISATION FORCÉE")
    print("=" * 60)
    
    # Utilisateur problématique identifié
    problematic_user = "mouharassoulmd@gmail.com"
    
    print(f"🎯 Synchronisation de l'utilisateur problématique: {problematic_user}")
    success = force_sync_user(problematic_user)
    
    if success:
        print(f"\n✅ Synchronisation terminée avec succès!")
        print(f"Vous pouvez maintenant tester avec: python verify_user.py")
    else:
        print(f"\n❌ Échec de la synchronisation")
        print("Vérifiez que Keycloak est accessible et les credentials sont corrects")

if __name__ == "__main__":
    main()
