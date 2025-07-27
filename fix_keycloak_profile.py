#!/usr/bin/env python3
"""
Script pour corriger automatiquement le profil utilisateur Keycloak
Résout les problèmes VERIFY_PROFILE et VERIFY_EMAIL
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
    
    def fix_keycloak_user_profile(user_email):
        """
        Corrige le profil utilisateur dans Keycloak pour éviter les écrans de vérification
        """
        try:
            print(f"🔧 Correction du profil Keycloak pour : {user_email}")
            
            # 1. Obtenir le token admin
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
            
            # 2. Rechercher l'utilisateur
            search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={user_email}&exact=true"
            search_resp = requests.get(search_url, headers=headers, timeout=10)
            
            if search_resp.status_code != 200 or not search_resp.json():
                print(f"❌ Utilisateur {user_email} non trouvé dans Keycloak")
                return False
                
            user_data = search_resp.json()[0]
            user_id = user_data['id']
            
            print(f"✅ Utilisateur trouvé - ID: {user_id}")
            print(f"   Nom actuel: {user_data.get('firstName', 'N/A')} {user_data.get('lastName', 'N/A')}")
            print(f"   Email vérifié: {user_data.get('emailVerified', False)}")
            print(f"   Actions requises: {user_data.get('requiredActions', [])}")
            
            # 3. Préparer les données de correction
            # Nettoyer le prénom (supprimer "Dr." s'il existe)
            first_name = user_data.get('firstName', '').replace('Dr.', '').strip()
            if not first_name:
                first_name = 'Utilisateur'  # Valeur par défaut
                
            last_name = user_data.get('lastName', '').strip()
            if not last_name:
                last_name = 'KeurDoctor'  # Valeur par défaut
            
            # Données de mise à jour
            update_data = {
                "firstName": first_name,
                "lastName": last_name,
                "email": user_email,
                "emailVerified": True,  # ✅ Marquer l'email comme vérifié
                "enabled": True,
                "requiredActions": []   # ✅ Supprimer toutes les actions requises
            }
            
            # 4. Mettre à jour le profil
            update_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}"
            update_resp = requests.put(update_url, json=update_data, headers=headers, timeout=10)
            
            if update_resp.status_code in (200, 204):
                print(f"✅ Profil mis à jour avec succès")
                print(f"   Nouveau prénom: '{first_name}'")
                print(f"   Nouveau nom: '{last_name}'")
                print(f"   Email vérifié: True")
                print(f"   Actions requises supprimées")
                
                # 5. Optionnel : Définir un mot de passe permanent si nécessaire
                password_data = {
                    "type": "password",
                    "value": "MotDePasseTemporaire123!",
                    "temporary": False  # Mot de passe permanent
                }
                
                pwd_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users/{user_id}/reset-password"
                pwd_resp = requests.put(pwd_url, json=password_data, headers=headers, timeout=10)
                
                if pwd_resp.status_code in (200, 204):
                    print(f"✅ Mot de passe permanent défini")
                else:
                    print(f"⚠️ Attention: Impossible de définir le mot de passe ({pwd_resp.status_code})")
                
                print(f"\n🎯 L'utilisateur peut maintenant se connecter sans écrans de vérification")
                return True
                
            else:
                print(f"❌ Erreur lors de la mise à jour: {update_resp.status_code} - {update_resp.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
            return False
    
    if __name__ == "__main__":
        # Utilisateur à corriger (modifiez selon vos besoins)
        user_to_fix = "mouharassoulm@gmail.com"
        
        print("=" * 60)
        print("🔧 CORRECTION PROFIL KEYCLOAK")
        print("=" * 60)
        
        success = fix_keycloak_user_profile(user_to_fix)
        
        if success:
            print(f"\n✅ Correction terminée avec succès pour {user_to_fix}")
            print("🎯 Actions à effectuer :")
            print("   1. Demander à l'utilisateur de se reconnecter")
            print("   2. Il ne devrait plus voir les écrans de vérification")
            print("   3. Si problème persiste, vérifier manuellement dans Keycloak Admin")
        else:
            print(f"\n❌ Échec de la correction pour {user_to_fix}")
            print("🔧 Actions manuelles recommandées :")
            print("   1. Accéder à Keycloak Admin Console")
            print("   2. Aller dans Users → Rechercher l'utilisateur")
            print("   3. Details → Cocher 'Email Verified'")
            print("   4. Supprimer les 'Required Actions'")
        
        print("=" * 60)
        
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    print("Assurez-vous d'être dans le bon répertoire du projet.")
