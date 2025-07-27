"""
Test complet : Vérifier que les rôles REALM et CLIENT sont assignés
Test spécifique pour résoudre le problème des rôles manquants
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

from comptes.models import Utilisateur
from comptes.keycloak_auto_sync import KeycloakSyncService
import requests
from django.conf import settings

print("=" * 80)
print("🎭 TEST COMPLET: RÔLES REALM + CLIENT + GROUPES KEYCLOAK")
print("=" * 80)

def test_keycloak_setup():
    """Test du setup automatique Keycloak"""
    print("\n1️⃣ SETUP AUTOMATIQUE KEYCLOAK")
    print("-" * 50)
    
    success = KeycloakSyncService.ensure_keycloak_setup()
    if success:
        print("✅ Setup Keycloak réussi")
        print("   📁 Groupes créés: administrateurs, médecins, patients")
        print("   🎭 Rôles realm créés: admin, medecin, patient, user")
    else:
        print("❌ Setup Keycloak échoué")
        return False
    
    return True

def test_user_complete_sync():
    """Test de création utilisateur avec synchronisation complète"""
    print("\n2️⃣ CRÉATION UTILISATEUR AVEC SYNC COMPLÈTE")
    print("-" * 50)
    
    test_email = "test.roles.complet@keurdoctor.com"
    
    # Supprimer l'utilisateur de test s'il existe
    try:
        existing_user = Utilisateur.objects.get(email=test_email)
        existing_user.delete()
        print(f"🧹 Utilisateur test existant supprimé")
    except Utilisateur.DoesNotExist:
        pass
    
    # Créer un utilisateur médecin pour test complet
    try:
        new_user = Utilisateur.objects.create_user(
            email=test_email,
            password="TestPassword123!",
            prenom="Dr. Marie",
            nom="MARTIN",
            role_autorise="medecin",
            is_staff=False,
            is_active=True
        )
        
        print(f"✅ Utilisateur Django créé: {new_user.email}")
        print(f"   🎭 Rôle: {new_user.role_autorise}")
        
        # Attendre la synchronisation
        import time
        time.sleep(3)
        
        # Vérifier dans Keycloak
        verification_success = verify_complete_keycloak_config(test_email, "medecin")
        
        return new_user, verification_success
        
    except Exception as e:
        print(f"❌ Erreur création utilisateur: {e}")
        return None, False

def verify_complete_keycloak_config(email, expected_role):
    """Vérifier que l'utilisateur a TOUT : profil + groupes + rôles realm + rôles client"""
    print("\n3️⃣ VÉRIFICATION COMPLÈTE KEYCLOAK")
    print("-" * 50)
    
    try:
        admin_token = KeycloakSyncService.get_admin_token()
        if not admin_token:
            print("❌ Token admin non obtenu")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 1. Vérifier l'utilisateur existe
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        search_resp = requests.get(search_url, headers=headers, timeout=10)
        
        if search_resp.status_code != 200 or not search_resp.json():
            print(f"❌ Utilisateur {email} non trouvé dans Keycloak")
            return False
        
        user_data = search_resp.json()[0]
        user_id = user_data['id']
        
        print(f"✅ Utilisateur trouvé:")
        print(f"   📧 Email: {user_data.get('email')}")
        print(f"   👤 Nom: {user_data.get('firstName')} {user_data.get('lastName')}")
        print(f"   ⚡ Activé: {user_data.get('enabled')}")
        print(f"   📧 Email vérifié: {user_data.get('emailVerified')}")
        
        # 2. Vérifier les GROUPES
        print(f"\n📁 VÉRIFICATION GROUPES:")
        groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups"
        groups_resp = requests.get(groups_url, headers=headers, timeout=10)
        
        groups_ok = False
        if groups_resp.status_code == 200:
            user_groups = [group.get('name') for group in groups_resp.json()]
            expected_group = 'médecins' if expected_role == 'medecin' else f"{expected_role}s"
            
            print(f"   Groupes assignés: {user_groups}")
            
            if expected_group in user_groups:
                print(f"   ✅ Groupe correct: {expected_group}")
                groups_ok = True
            else:
                print(f"   ❌ Groupe {expected_group} MANQUANT")
        
        # 3. Vérifier les RÔLES REALM
        print(f"\n🎭 VÉRIFICATION RÔLES REALM:")
        realm_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
        realm_roles_resp = requests.get(realm_roles_url, headers=headers, timeout=10)
        
        realm_roles_ok = False
        if realm_roles_resp.status_code == 200:
            user_realm_roles = [role.get('name') for role in realm_roles_resp.json()]
            expected_realm_roles = ['user', expected_role, 'offline_access']
            
            print(f"   Rôles realm assignés: {user_realm_roles}")
            
            missing_realm_roles = []
            for expected in expected_realm_roles:
                if expected not in user_realm_roles:
                    missing_realm_roles.append(expected)
            
            if not missing_realm_roles:
                print(f"   ✅ Tous les rôles realm présents")
                realm_roles_ok = True
            else:
                print(f"   ❌ Rôles realm MANQUANTS: {missing_realm_roles}")
        
        # 4. Vérifier les RÔLES CLIENT
        print(f"\n🔧 VÉRIFICATION RÔLES CLIENT:")
        client_id = settings.OIDC_RP_CLIENT_ID
        
        # Récupérer l'UUID du client
        clients_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/clients"
        clients_resp = requests.get(clients_url, headers=headers, timeout=10)
        
        client_uuid = None
        if clients_resp.status_code == 200:
            for client in clients_resp.json():
                if client.get('clientId') == client_id:
                    client_uuid = client['id']
                    break
        
        client_roles_ok = False
        if client_uuid:
            client_roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/clients/{client_uuid}"
            client_roles_resp = requests.get(client_roles_url, headers=headers, timeout=10)
            
            if client_roles_resp.status_code == 200:
                user_client_roles = [role.get('name') for role in client_roles_resp.json()]
                expected_client_roles = ['user', expected_role]
                
                print(f"   Rôles client assignés: {user_client_roles}")
                
                missing_client_roles = []
                for expected in expected_client_roles:
                    if expected not in user_client_roles:
                        missing_client_roles.append(expected)
                
                if not missing_client_roles:
                    print(f"   ✅ Tous les rôles client présents")
                    client_roles_ok = True
                else:
                    print(f"   ❌ Rôles client MANQUANTS: {missing_client_roles}")
        else:
            print(f"   ⚠️ Client {client_id} non trouvé")
        
        # 5. RÉSULTAT FINAL
        print(f"\n📊 RÉSUMÉ VÉRIFICATION:")
        print(f"   Profil utilisateur: ✅")
        print(f"   Groupes: {'✅' if groups_ok else '❌'}")
        print(f"   Rôles realm: {'✅' if realm_roles_ok else '❌'}")
        print(f"   Rôles client: {'✅' if client_roles_ok else '❌'}")
        
        complete_success = groups_ok and realm_roles_ok and client_roles_ok
        
        if complete_success:
            print(f"\n🎯 SUCCÈS COMPLET: Utilisateur peut se connecter!")
        else:
            print(f"\n❌ CONFIGURATION INCOMPLÈTE: Problèmes détectés")
        
        return complete_success
        
    except Exception as e:
        print(f"❌ Erreur vérification: {e}")
        return False

def cleanup_test_user(email):
    """Nettoyer l'utilisateur de test"""
    try:
        # Django
        user = Utilisateur.objects.get(email=email)
        user.delete()
        print(f"🧹 Utilisateur Django nettoyé")
        
        # Keycloak
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
                    print(f"🧹 Utilisateur Keycloak nettoyé")
                    
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")

if __name__ == "__main__":
    try:
        # 1. Setup Keycloak
        setup_ok = test_keycloak_setup()
        
        if setup_ok:
            # 2. Test utilisateur complet
            user, verification_ok = test_user_complete_sync()
            
            print("\n" + "=" * 80)
            if verification_ok:
                print("🏆 RÉSULTAT: CORRECTION RÔLES RÉUSSIE!")
                print("=" * 80)
                print("✅ Rôles REALM assignés correctement")
                print("✅ Rôles CLIENT assignés correctement")
                print("✅ Groupes Keycloak assignés correctement")
                print("✅ L'utilisateur peut maintenant se connecter!")
                print("✅ Plus de problème d'authentification OIDC")
            else:
                print("❌ RÉSULTAT: PROBLÈMES PERSISTENT")
                print("=" * 80)
                print("❌ Des rôles ou groupes sont encore manquants")
                print("❌ Vérifiez les logs ci-dessus pour les détails")
            
            # Nettoyage
            if user:
                print(f"\n🧹 Nettoyage...")
                cleanup_test_user(user.email)
        else:
            print("❌ Setup Keycloak échoué - impossible de continuer")
        
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Erreur générale: {e}")
        import traceback
        traceback.print_exc()

print("\nAppuyez sur Entrée pour continuer...")
input()
