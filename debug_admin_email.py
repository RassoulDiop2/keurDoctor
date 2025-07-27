#!/usr/bin/env python3
"""
Script pour diagnostiquer le problème d'email manquant lors de la création via formulaire admin
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.admin import UtilisateurCreationForm
from comptes.keycloak_auto_sync import KeycloakSyncService
import requests
from django.conf import settings
import logging

# Configuration du logging détaillé
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_keycloak_admin_token():
    """Obtenir token admin Keycloak"""
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

def check_user_in_keycloak_detailed(email):
    """Vérifier utilisateur dans Keycloak avec détails"""
    
    admin_token = get_keycloak_admin_token()
    if not admin_token:
        print("❌ Impossible d'obtenir le token admin")
        return None
    
    try:
        headers = {'Authorization': f'Bearer {admin_token}'}
        search_url = f"{settings.KEYCLOAK_SERVER_URL}/admin/realms/{settings.OIDC_REALM}/users?email={email}&exact=true"
        
        response = requests.get(search_url, headers=headers, timeout=10)
        if response.status_code == 200:
            users = response.json()
            if users:
                user_data = users[0]
                print(f"🔍 UTILISATEUR KEYCLOAK DÉTAILLÉ:")
                print(f"   ID: {user_data.get('id')}")
                print(f"   Username: {user_data.get('username')}")
                print(f"   Email: '{user_data.get('email', 'NON DÉFINI')}' (type: {type(user_data.get('email'))})")
                print(f"   FirstName: '{user_data.get('firstName', 'NON DÉFINI')}'")
                print(f"   LastName: '{user_data.get('lastName', 'NON DÉFINI')}'")
                print(f"   Enabled: {user_data.get('enabled')}")
                print(f"   EmailVerified: {user_data.get('emailVerified')}")
                print(f"   Attributes: {user_data.get('attributes', {})}")
                
                return user_data
            else:
                print(f"❌ Utilisateur {email} non trouvé dans Keycloak")
                return None
        else:
            print(f"❌ Erreur recherche Keycloak: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return None

def test_admin_form_creation():
    """Test complet de création via formulaire admin"""
    
    print("🧪 TEST CRÉATION VIA FORMULAIRE ADMIN")
    print("=" * 70)
    
    # Email de test unique
    from datetime import datetime
    test_email = f"test.admin.debug.{datetime.now().strftime('%H%M%S')}@example.com"
    
    # Supprimer s'il existe
    Utilisateur.objects.filter(email=test_email).delete()
    
    # Données du formulaire
    form_data = {
        'email': test_email,
        'nom': 'AdminDebug',
        'prenom': 'Test',
        'role_autorise': 'patient',
        'est_actif': True,
        'password1': 'TestPass123!',
        'password2': 'TestPass123!'
    }
    
    print(f"📝 ÉTAPE 1 - Données formulaire:")
    print(f"   Email: {form_data['email']}")
    print(f"   Nom: {form_data['nom']}")
    print(f"   Prénom: {form_data['prenom']}")
    print(f"   Rôle: {form_data['role_autorise']}")
    
    # Créer le formulaire
    print(f"\n🔧 ÉTAPE 2 - Validation formulaire...")
    form = UtilisateurCreationForm(data=form_data)
    
    if not form.is_valid():
        print(f"❌ Formulaire invalide:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return
    
    print("✅ Formulaire valide")
    
    # Sauvegarder (déclenchera les signaux)
    print(f"\n💾 ÉTAPE 3 - Sauvegarde (déclenchement des signaux)...")
    
    # Activer le logging détaillé temporairement
    logging.getLogger('comptes.keycloak_auto_sync').setLevel(logging.DEBUG)
    
    user = form.save()
    
    print(f"✅ Utilisateur Django créé:")
    print(f"   ID: {user.id}")
    print(f"   Email: '{user.email}' (type: {type(user.email)})")
    print(f"   Prénom: '{user.prenom}'")
    print(f"   Nom: '{user.nom}'")
    print(f"   Rôle: '{user.role_autorise}'")
    
    # Attendre un peu pour la synchronisation
    print(f"\n⏳ ÉTAPE 4 - Attente synchronisation (3 secondes)...")
    import time
    time.sleep(3)
    
    # Vérifier dans Keycloak
    print(f"\n🔍 ÉTAPE 5 - Vérification dans Keycloak...")
    keycloak_user = check_user_in_keycloak_detailed(test_email)
    
    if keycloak_user:
        email_in_keycloak = keycloak_user.get('email')
        if email_in_keycloak and email_in_keycloak.strip():
            print(f"✅ EMAIL CORRECTEMENT SYNCHRONISÉ!")
        else:
            print(f"❌ EMAIL MANQUANT OU VIDE dans Keycloak!")
            print(f"🔧 Tentative de synchronisation manuelle...")
            
            # Forcer la synchronisation
            success = KeycloakSyncService.ensure_user_complete_profile(user)
            if success:
                print("✅ Synchronisation manuelle réussie")
                time.sleep(2)
                check_user_in_keycloak_detailed(test_email)
            else:
                print("❌ Synchronisation manuelle échouée")
    else:
        print(f"❌ Utilisateur non trouvé dans Keycloak - Synchronisation ratée!")
    
    return user

def main():
    print("🚀 DIAGNOSTIC PROBLÈME EMAIL FORMULAIRE ADMIN")
    print("=" * 70)
    
    test_admin_form_creation()

if __name__ == "__main__":
    main()
