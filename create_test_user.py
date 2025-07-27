#!/usr/bin/env python3
"""
Script pour créer un utilisateur de test via l'interface admin
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.admin import UtilisateurCreationForm
from django.contrib.auth.models import User
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_user():
    """Créer un utilisateur de test"""
    print("🔧 CRÉATION D'UN UTILISATEUR DE TEST")
    print("=" * 60)
    
    # Données de test
    test_data = {
        'email': 'test.synchronisation@example.com',
        'nom': 'TestSync',
        'prenom': 'Utilisateur',
        'role_autorise': 'patient',
        'est_actif': True,
        'password1': 'TestPassword123!',
        'password2': 'TestPassword123!'
    }
    
    print(f"📝 Données utilisateur:")
    for key, value in test_data.items():
        if 'password' not in key:
            print(f"   {key}: {value}")
    
    try:
        # Vérifier si l'utilisateur existe déjà
        existing_user = Utilisateur.objects.filter(email=test_data['email']).first()
        if existing_user:
            print(f"⚠️  Utilisateur {test_data['email']} existe déjà (créé le {existing_user.date_creation})")
            
            # Supprimer pour recréer
            print("🗑️  Suppression de l'utilisateur existant...")
            existing_user.delete()
            print("✅ Utilisateur supprimé")
        
        # Créer le formulaire
        print(f"\n📋 Création du formulaire...")
        form = UtilisateurCreationForm(data=test_data)
        
        if form.is_valid():
            print("✅ Formulaire valide")
            
            # Sauvegarder
            print("💾 Sauvegarde de l'utilisateur...")
            user = form.save()
            
            print(f"✅ Utilisateur créé avec succès!")
            print(f"   ID: {user.id}")
            print(f"   Email: {user.email}")
            print(f"   Nom: {user.nom}")
            print(f"   Prénom: {user.prenom}")
            print(f"   Rôle: {user.role_autorise}")
            print(f"   Actif: {user.est_actif}")
            
            return user
            
        else:
            print(f"❌ Erreurs de formulaire:")
            for field, errors in form.errors.items():
                print(f"   {field}: {errors}")
            return None
            
    except Exception as e:
        print(f"❌ Erreur lors de la création: {e}")
        logger.exception("Erreur détaillée:")
        return None

if __name__ == "__main__":
    user = create_test_user()
    if user:
        print(f"\n🎉 Utilisateur {user.email} créé avec succès!")
        print("Vous pouvez maintenant tester sa synchronisation avec Keycloak")
    else:
        print(f"\n❌ Échec de la création de l'utilisateur")
