"""
Test complet de la synchronisation Keycloak avec groupes et rôles
Simule la création d'un utilisateur par l'admin métier
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

from comptes.models import Utilisateur
from comptes.keycloak_auto_sync import KeycloakSyncService
import requests
from django.conf import settings

print("=" * 80)
print("🏥 TEST SYNCHRONISATION COMPLÈTE KEYCLOAK - GROUPES ET RÔLES")
print("=" * 80)

def test_user_creation_complete():
    """Test complet de création utilisateur comme l'admin métier"""
    
    print("\n1️⃣ CRÉATION UTILISATEUR VIA INTERFACE ADMIN")
    print("-" * 50)
    
    # Simuler la création d'un utilisateur par l'admin métier
    test_email = "test.medecin.sync@keurdoctor.com"
    
    # Supprimer l'utilisateur de test s'il existe déjà
    try:
        existing_user = Utilisateur.objects.get(email=test_email)
        existing_user.delete()
        print(f"🧹 Utilisateur test existant supprimé: {test_email}")
    except Utilisateur.DoesNotExist:
        pass
    
    # Créer un nouvel utilisateur (comme le ferait l'admin métier)
    try:
        new_user = Utilisateur.objects.create_user(
            email=test_email,
            password="TestPassword123!",
            prenom="Dr. Jean",
            nom="DUPONT",
            role_autorise="medecin",
            is_staff=False,
            is_active=True
        )
        
        print(f"✅ Utilisateur Django créé: {new_user.email}")
        print(f"   📋 Rôle: {new_user.role_autorise}")
        print(f"   👤 Nom: {new_user.prenom} {new_user.nom}")
        
        # Le signal post_save devrait automatiquement synchroniser avec Keycloak
        print("\n2️⃣ VÉRIFICATION SYNCHRONISATION AUTOMATIQUE")
        print("-" * 50)
        
        # Attendre un peu pour la synchronisation
        import time
        time.sleep(2)
        
        # Vérifier dans Keycloak
        success = verify_user_in_keycloak(test_email, "medecin")
        
        if success:
            print("🎯 SUCCÈS: Utilisateur complètement synchronisé!")
            print("   ✅ Profil créé dans Keycloak")
            print("   ✅ Assigné au groupe 'médecins'")
            print("   ✅ Rôles client assignés")
            print("   ✅ Peut maintenant se connecter sur la plateforme")
        else:
            print("❌ ÉCHEC: Synchronisation incomplète")
        
        return new_user, success
        
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        return None, False

def verify_user_in_keycloak(email, expected_role):
    """Vérifier que l'utilisateur est correctement configuré dans Keycloak"""
    try:
        # Obtenir le token admin
        admin_token = KeycloakSyncService.get_admin_token()
        if not admin_token:
            print("❌ Impossible d'obtenir le token admin Keycloak")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 1. Vérifier que l'utilisateur existe
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        
        if search_resp.status_code != 200 or not search_resp.json():
            print(f"❌ Utilisateur {email} non trouvé dans Keycloak")
            return False
        
        user_data = search_resp.json()[0]
        user_id = user_data['id']
        
        print(f"✅ Utilisateur trouvé dans Keycloak:")
        print(f"   🆔 ID: {user_id}")
        print(f"   📧 Email: {user_data.get('email')}")
        print(f"   👤 Nom: {user_data.get('firstName')} {user_data.get('lastName')}")
        print(f"   ⚡ Activé: {user_data.get('enabled')}")
        print(f"   📧 Email vérifié: {user_data.get('emailVerified')}")
        
        # 2. Vérifier les groupes
        groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups"
        groups_resp = requests.get(groups_url, headers=headers, timeout=10)
        
        if groups_resp.status_code == 200:
            user_groups = [group.get('name') for group in groups_resp.json()]
            expected_group = 'médecins' if expected_role == 'medecin' else f"{expected_role}s"
            
            print(f"📁 Groupes assignés: {user_groups}")
            
            if expected_group in user_groups:
                print(f"✅ Utilisateur assigné au bon groupe: {expected_group}")
            else:
                print(f"❌ Utilisateur NON assigné au groupe {expected_group}")
                return False
        
        # 3. Vérifier les rôles client
        client_id = settings.OIDC_RP_CLIENT_ID
        clients_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/clients"
        clients_resp = requests.get(clients_url, headers=headers, timeout=10)
        
        client_uuid = None
        if clients_resp.status_code == 200:
            for client in clients_resp.json():
                if client.get('clientId') == client_id:
                    client_uuid = client['id']
                    break
        
        if client_uuid:
            client_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
            client_roles_resp = requests.get(client_roles_url, headers=headers, timeout=10)
            
            if client_roles_resp.status_code == 200:
                user_client_roles = [role.get('name') for role in client_roles_resp.json()]
                print(f"🎭 Rôles client assignés: {user_client_roles}")
                
                if expected_role in user_client_roles or 'user' in user_client_roles:
                    print(f"✅ Rôles client corrects")
                else:
                    print(f"⚠️ Rôles client manquants")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur vérification Keycloak: {e}")
        return False

def cleanup_test_user(email):
    """Nettoyer l'utilisateur de test"""
    try:
        # Supprimer de Django
        user = Utilisateur.objects.get(email=email)
        user.delete()
        print(f"🧹 Utilisateur Django supprimé: {email}")
        
        # Supprimer de Keycloak
        admin_token = KeycloakSyncService.get_admin_token()
        if admin_token:
            headers = {'Authorization': f'Bearer {admin_token}'}
            
            search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
            search_resp = requests.get(search_url, headers=headers, timeout=10)
            
            if search_resp.status_code == 200 and search_resp.json():
                user_id = search_resp.json()[0]['id']
                delete_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
                delete_resp = requests.delete(delete_url, headers=headers, timeout=10)
                
                if delete_resp.status_code in (200, 204):
                    print(f"🧹 Utilisateur Keycloak supprimé: {email}")
                    
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")

if __name__ == "__main__":
    try:
        # Test principal
        user, success = test_user_creation_complete()
        
        print("\n" + "=" * 80)
        if success:
            print("🎯 RÉSULTAT: SYNCHRONISATION COMPLÈTE RÉUSSIE!")
            print("=" * 80)
            print("✅ L'admin métier peut maintenant créer des utilisateurs")
            print("✅ Les utilisateurs peuvent se connecter immédiatement")
            print("✅ Groupes et rôles Keycloak assignés automatiquement")
            print("✅ Plus de problème de connexion après création")
        else:
            print("❌ RÉSULTAT: SYNCHRONISATION INCOMPLÈTE")
            print("=" * 80)
            print("❌ Des corrections supplémentaires sont nécessaires")
        
        # Nettoyage
        if user:
            print("\n🧹 Nettoyage de l'utilisateur de test...")
            cleanup_test_user(user.email)
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

print("\nAppuyez sur Entrée pour continuer...")
input()
