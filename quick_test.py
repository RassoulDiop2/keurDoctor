#!/usr/bin/env python3
"""
Script pour tester la création d'utilisateur via Django shell
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.admin import UtilisateurCreationForm

def test_user_creation():
    """Test rapide de création d'utilisateur"""
    
    # Supprimer l'utilisateur de test s'il existe
    Utilisateur.objects.filter(email='test.admin@example.com').delete()
    
    # Données de test
    form_data = {
        'email': 'test.admin@example.com',  
        'nom': 'TestAdmin',
        'prenom': 'Utilisateur',
        'role_autorise': 'medecin',
        'est_actif': True,
        'password1': 'TestPass123!',
        'password2': 'TestPass123!'
    }
    
    print("=== TEST CRÉATION UTILISATEUR ===")
    print(f"Email: {form_data['email']}")
    print(f"Rôle: {form_data['role_autorise']}")
    
    # Créer le formulaire
    form = UtilisateurCreationForm(data=form_data)
    
    if form.is_valid():
        print("✅ Formulaire valide")
        user = form.save()
        print(f"✅ Utilisateur créé: {user.email}")
        print(f"   ID: {user.id}")
        print(f"   Email: {user.email}")
        print(f"   Rôle: {user.role_autorise}")
        
        # Vérifier si l'email est bien défini
        if user.email:
            print("✅ Email correctement défini dans Django")
        else:
            print("❌ Email manquant dans Django")
            
        return user
    else:
        print("❌ Erreurs de formulaire:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return None

if __name__ == "__main__":
    test_user_creation()

print("\n🎉 Test terminé!")
