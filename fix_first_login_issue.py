#!/usr/bin/env python3
"""
Script pour corriger le problème de première connexion utilisateur
Résout l'erreur lors de la mise à jour des identifiants
"""
import os
import sys
import django
import requests
import json

# Configuration Django
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

try:
    django.setup()
    from django.conf import settings
    from comptes.models import Utilisateur
    
    def fix_first_login_issue(user_email):
        """
        Corrige le problème de première connexion en supprimant les actions requises
        et en définissant un mot de passe permanent
        """
        try:
            print(f"🔧 Correction première connexion pour : {user_email}")
            
            # 1. Vérifier l'utilisateur Django
            try:
                user = Utilisateur.objects.get(email=user_email)
                print(f"✅ Utilisateur Django trouvé: {user.prenom} {user.nom}")
            except Utilisateur.DoesNotExist:
                print(f"❌ Utilisateur {user_email} non trouvé dans Django")
                return False
            
            # 2. Obtenir le token admin
            token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
            token_data = {
                'grant_type': 'password',
                'client_id': 'admin-cli',
                'username': settings.KEYCLOAK_ADMIN_USER,
                'password': settings.KEYCLOAK_ADMIN_PASSWORD
            }
            
            token_response = requests.post(token_url, data=token_data, timeout=10)
            if token_response.status_code != 200:
                print(f"❌ Erreur token admin: {token_response.status_code}")
                return False
                
            admin_token = token_response.json()['access_token']
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            # 3. Rechercher l'utilisateur dans Keycloak
            search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={user_email}&exact=true"
            search_resp = requests.get(search_url, headers=headers, timeout=10)
            
            if search_resp.status_code != 200 or not search_resp.json():
                print(f"❌ Utilisateur {user_email} non trouvé dans Keycloak")
                return False
                
            user_data = search_resp.json()[0]
            user_id = user_data['id']
            
            print(f"✅ Utilisateur Keycloak trouvé - ID: {user_id}")
            print(f"   Actions requises actuelles: {user_data.get('requiredActions', [])}")
            print(f"   Email vérifié: {user_data.get('emailVerified', False)}")
            
            # 4. Préparer les données de correction
            # Nettoyer le prénom (supprimer "Dr." s'il existe)
            first_name = user.prenom.replace('Dr.', '').replace('Dr', '').strip() if user.prenom else 'Utilisateur'
            last_name = user.nom.strip() if user.nom else 'KeurDoctor'
            
            # Données de mise à jour COMPLÈTES
            update_data = {
                "username": user.email,
                "email": user.email,
                "firstName": first_name,
                "lastName": last_name,
                "enabled": True,
                "emailVerified": True,  # ✅ Marquer l'email comme vérifié
                "requiredActions": [],   # ✅ Supprimer toutes les actions requises
                "attributes": {
                    "role": [user.role_autorise or 'patient']
                }
            }
            
            # 5. Mettre à jour le profil
            update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
            update_resp = requests.put(update_url, json=update_data, headers=headers, timeout=10)
            
            if update_resp.status_code in (200, 204):
                print(f"✅ Profil mis à jour avec succès")
                print(f"   Prénom: '{first_name}'")
                print(f"   Nom: '{last_name}'")
                print(f"   Email vérifié: True")
                print(f"   Actions requises supprimées")
                
                # 6. Définir un mot de passe permanent (non temporaire)
                password_data = {
                    "type": "password",
                    "value": "MotDePasseTemporaire123!",  # Mot de passe par défaut
                    "temporary": False  # ✅ Mot de passe permanent (pas de changement forcé)
                }
                
                pwd_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/reset-password"
                pwd_resp = requests.put(pwd_url, json=password_data, headers=headers, timeout=10)
                
                if pwd_resp.status_code in (200, 204):
                    print(f"✅ Mot de passe permanent défini")
                    print(f"   Mot de passe: MotDePasseTemporaire123!")
                    print(f"   Changement forcé: NON")
                else:
                    print(f"⚠️ Attention: Impossible de définir le mot de passe ({pwd_resp.status_code})")
                
                # 7. Vérifier que les groupes et rôles sont assignés
                print(f"\n🔍 Vérification des groupes et rôles...")
                
                # Vérifier les groupes
                groups_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/groups"
                groups_resp = requests.get(groups_url, headers=headers, timeout=10)
                
                if groups_resp.status_code == 200:
                    user_groups = groups_resp.json()
                    group_names = [g['name'] for g in user_groups]
                    print(f"   Groupes assignés: {group_names}")
                else:
                    print(f"   ⚠️ Impossible de vérifier les groupes")
                
                # Vérifier les rôles realm
                roles_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/role-mappings/realm"
                roles_resp = requests.get(roles_url, headers=headers, timeout=10)
                
                if roles_resp.status_code == 200:
                    user_roles = roles_resp.json()
                    role_names = [r['name'] for r in user_roles]
                    print(f"   Rôles realm assignés: {role_names}")
                else:
                    print(f"   ⚠️ Impossible de vérifier les rôles")
                
                print(f"\n🎯 L'utilisateur peut maintenant se connecter sans écrans de vérification")
                print(f"📧 Email: {user.email}")
                print(f"🔐 Mot de passe: MotDePasseTemporaire123!")
                print(f"🌐 URL de connexion: http://localhost:8000")
                
                return True
                
            else:
                print(f"❌ Erreur lors de la mise à jour: {update_resp.status_code} - {update_resp.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
            return False
    
    def fix_all_users_first_login():
        """
        Corrige le problème de première connexion pour tous les utilisateurs
        """
        print("🔧 CORRECTION PREMIÈRE CONNEXION - TOUS LES UTILISATEURS")
        print("=" * 70)
        
        # Récupérer tous les utilisateurs Django
        users = Utilisateur.objects.filter(est_actif=True)
        print(f"📊 Utilisateurs à traiter: {users.count()}")
        
        success_count = 0
        error_count = 0
        
        for user in users:
            print(f"\n{'='*50}")
            print(f"👤 Traitement: {user.email}")
            
            if fix_first_login_issue(user.email):
                success_count += 1
                print(f"✅ Succès pour {user.email}")
            else:
                error_count += 1
                print(f"❌ Échec pour {user.email}")
        
        print(f"\n{'='*70}")
        print(f"📊 RÉSUMÉ:")
        print(f"   ✅ Succès: {success_count}")
        print(f"   ❌ Échecs: {error_count}")
        print(f"   📈 Total: {users.count()}")
        
        if success_count > 0:
            print(f"\n🎉 Correction terminée!")
            print(f"💡 Les utilisateurs peuvent maintenant se connecter sans problème")
            print(f"🔐 Mot de passe par défaut: MotDePasseTemporaire123!")
        
        return success_count, error_count
    
    if __name__ == "__main__":
        import argparse
        
        parser = argparse.ArgumentParser(description="Corriger le problème de première connexion")
        parser.add_argument("--email", help="Email de l'utilisateur à corriger")
        parser.add_argument("--all", action="store_true", help="Corriger tous les utilisateurs")
        
        args = parser.parse_args()
        
        if args.all:
            fix_all_users_first_login()
        elif args.email:
            success = fix_first_login_issue(args.email)
            if success:
                print(f"\n✅ Correction réussie pour {args.email}")
            else:
                print(f"\n❌ Échec de la correction pour {args.email}")
        else:
            print("🔧 CORRECTION PREMIÈRE CONNEXION")
            print("=" * 50)
            print("Usage:")
            print("  python fix_first_login_issue.py --email user@example.com")
            print("  python fix_first_login_issue.py --all")
            print("\nExemple:")
            print("  python fix_first_login_issue.py --email rassoulmouhamd2@gmail.com")
        
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    print("Assurez-vous d'être dans le bon répertoire du projet.") 