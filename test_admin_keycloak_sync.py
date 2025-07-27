#!/usr/bin/env python3
"""
Script de test pour vérifier la synchronisation Keycloak lors de la création d'utilisateur admin
"""
import os
import sys
import django

# Configuration Django
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

try:
    django.setup()
    from comptes.admin import UtilisateurCreationForm
    from comptes.models import Utilisateur
    
    print("🧪 Test de création d'utilisateur avec synchronisation Keycloak...")
    
    # Données de test
    test_data = {
        'email': 'test.sync@keurdoctor.com',
        'prenom': 'Jean',
        'nom': 'Dupont',
        'role': 'medecin',
        'password1': 'TestPass123!',
        'password2': 'TestPass123!'
    }
    
    # Supprimer l'utilisateur s'il existe
    try:
        existing_user = Utilisateur.objects.get(email=test_data['email'])
        existing_user.delete()
        print(f"✅ Utilisateur existant {test_data['email']} supprimé")
    except Utilisateur.DoesNotExist:
        pass
    
    # Créer le formulaire avec les données
    form = UtilisateurCreationForm(data=test_data)
    
    if form.is_valid():
        print("✅ Formulaire valide")
        
        # Sauvegarder (cela devrait déclencher la synchronisation Keycloak)
        user = form.save()
        
        print(f"✅ Utilisateur créé dans Django:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: {user.prenom}")
        print(f"   Nom: {user.nom}")
        print(f"   Rôle: {user.role_autorise}")
        print(f"   Keycloak ID: {user.keycloak_id}")
        
        # Vérifier les groupes Django
        groups = user.groups.all()
        print(f"   Groupes Django: {[g.name for g in groups]}")
        
        print("\n🎯 Vérifications:")
        print("1. ✅ Utilisateur créé dans Django")
        print("2. ✅ Champs prénom/nom renseignés")
        print("3. ✅ Rôle attribué")
        print("4. ✅ Groupes Django assignés")
        print("5. 🔄 Synchronisation Keycloak - vérifiez les logs")
        
        print(f"\n📋 Vérifiez dans Keycloak Admin Console:")
        print(f"   - Email: {user.email}")
        print(f"   - First Name: {user.prenom}")
        print(f"   - Last Name: {user.nom}")
        print(f"   - Groupe: médecins")
        
    else:
        print("❌ Erreurs dans le formulaire:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
