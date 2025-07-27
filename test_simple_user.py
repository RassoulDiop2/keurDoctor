#!/usr/bin/env python3
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur

# Test simple
print("=== CRÉATION UTILISATEUR SIMPLE ===")

# Supprimer s'il existe
Utilisateur.objects.filter(email='test.simple@example.com').delete()

# Créer directement
user = Utilisateur.objects.create_user(
    email='test.simple@example.com',
    prenom='Test',
    nom='Simple',
    password='TestPass123!',
    role_autorise='patient'
)

print(f"✅ Utilisateur créé: {user.email}")
print(f"   ID: {user.id}")
print(f"   Email: {user.email}")
print(f"   Rôle: {user.role_autorise}")
print(f"   Actif: {user.est_actif}")

# Vérifier dans Keycloak après synchronisation
print("\n⏳ Attente de 3 secondes pour la synchronisation...")
import time
time.sleep(3)

# Vérifier la synchronisation Keycloak
from comptes.keycloak_auto_sync import KeycloakSyncService
import requests
from django.conf import settings

def get_keycloak_admin_token():
    try:
        token_url = f"{settings.KEYCLOAK_SERVER_URL}/realms/master/protocol/openid-connect/token"
        token_data = {
            'grant_type': 'password',
            'client_id': 'admin-cli',
            'username': settings.KEYCLOAK_ADMIN_USER,
            'password': settings.KEYCLOAK_ADMIN_PASSWORD
        }
        
        response = requests.post(token_url, data=token_data, timeout=10)
        if response.status_code == 200:
            return response.json()['access_token']
        return None
    except:
        return None

def check_user_in_keycloak(email, admin_token):
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            return users[0] if users else None
        return None
    except:
        return None

print("🔍 Vérification dans Keycloak...")
admin_token = get_keycloak_admin_token()
if admin_token:
    keycloak_user = check_user_in_keycloak(user.email, admin_token)
    if keycloak_user:
        print(f"✅ Utilisateur trouvé dans Keycloak:")
        print(f"   Email: {keycloak_user.get('email', 'NON DÉFINI ❌')}")
        print(f"   Username: {keycloak_user.get('username')}")
    else:
        print("❌ Utilisateur non trouvé dans Keycloak")
        print("🔧 Tentative de synchronisation manuelle...")
        success = KeycloakSyncService.ensure_user_complete_profile(user)
        print(f"Résultat: {'Succès' if success else 'Échec'}")
else:
    print("❌ Impossible de se connecter à Keycloak")

print("\n✅ Test terminé")
