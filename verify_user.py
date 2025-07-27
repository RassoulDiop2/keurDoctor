#!/usr/bin/env python3
"""
Script pour vérifier un utilisateur spécifique après création
"""
import os
import django
import requests

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur

def verify_user_sync(email):
    """Vérifier la synchronisation d'un utilisateur spécifique"""
    
    print(f"🔍 VÉRIFICATION UTILISATEUR: {email}")
    print("=" * 60)
    
    # 1. Vérifier dans Django
    try:
        user = Utilisateur.objects.get(email=email)
        print(f"✅ Utilisateur Django trouvé:")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Username: {user.username}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
        print(f"   Actif: {user.est_actif}")
        print(f"   Créé: {user.date_creation}")
        
        # Vérifications de base
        if user.email == user.username:
            print("✅ Email = Username (correct)")
        else:
            print(f"❌ Email ≠ Username ({user.email} ≠ {user.username})")
            
    except Utilisateur.DoesNotExist:
        print(f"❌ Utilisateur {email} non trouvé dans Django")
        return False
    
    # 2. Vérifier dans Keycloak
    print(f"\n🔑 Vérification dans Keycloak...")
    
    try:
        # Obtenir token admin
        token_url = "http://localhost:8080/realms/master/protocol/openid-connect/token"
        token_data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': 'admin',
            'password': 'admin'
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Impossible d'obtenir le token admin: {response.status_code}")
            return False
            
        admin_token = response.json()['access_token']
        
        # Rechercher l'utilisateur
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"http://localhost:8080/admin/realms/KeurDoctorSecure/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                keycloak_user = users[0]
                print(f"✅ Utilisateur Keycloak trouvé:")
                print(f"   ID: {keycloak_user.get('id')}")
                print(f"   Username: {keycloak_user.get('username')}")
                print(f"   Email: {keycloak_user.get('email', 'NON DÉFINI ❌')}")
                print(f"   Prénom: {keycloak_user.get('firstName', 'NON DÉFINI')}")
                print(f"   Nom: {keycloak_user.get('lastName', 'NON DÉFINI')}")
                print(f"   Activé: {keycloak_user.get('enabled')}")
                print(f"   Email vérifié: {keycloak_user.get('emailVerified')}")
                
                # Vérifications critiques
                if keycloak_user.get('email'):
                    print("✅ Email présent dans Keycloak")
                else:
                    print("❌ Email MANQUANT dans Keycloak - PROBLÈME!")
                    
                if keycloak_user.get('username') == email:
                    print("✅ Username = Email dans Keycloak")
                else:
                    print(f"⚠️  Username ≠ Email dans Keycloak")
                    
                return True
            else:
                print(f"❌ Utilisateur {email} NON TROUVÉ dans Keycloak")
                return False
        else:
            print(f"❌ Erreur recherche Keycloak: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur vérification Keycloak: {e}")
        return False

def main():
    print("🔍 VÉRIFICATEUR D'UTILISATEUR")
    print("=" * 60)
    
    # Proposer les derniers utilisateurs créés
    recent_users = Utilisateur.objects.order_by('-date_creation')[:3]
    if recent_users:
        print("📋 Derniers utilisateurs créés:")
        for i, user in enumerate(recent_users, 1):
            print(f"{i}. {user.email} - {user.date_creation}")
        
        print(f"\nEntrez l'email à vérifier (ou laissez vide pour le plus récent):")
        email_input = input().strip()
        
        if not email_input:
            email_to_check = recent_users[0].email
        else:
            email_to_check = email_input
            
        print(f"\n🎯 Vérification de: {email_to_check}")
        result = verify_user_sync(email_to_check)
        
        if result:
            print(f"\n✅ Utilisateur {email_to_check} correctement synchronisé!")
        else:
            print(f"\n❌ Problème de synchronisation pour {email_to_check}")
            
    else:
        print("❌ Aucun utilisateur trouvé dans la base de données")

if __name__ == "__main__":
    main()
