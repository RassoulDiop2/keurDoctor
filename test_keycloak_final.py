import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.admin import UtilisateurCreationForm

print("=== Test Synchronisation Keycloak Admin ===")

# Données de test
test_data = {
    'email': 'test.keycloak@keurdoctor.com',
    'prenom': 'Marie',
    'nom': 'Martin',
    'role': 'medecin',
    'password1': 'TestKeycloak123!',
    'password2': 'TestKeycloak123!'
}

# Supprimer utilisateur existant
try:
    existing = Utilisateur.objects.get(email=test_data['email'])
    existing.delete()
    print("✅ Utilisateur existant supprimé")
except Utilisateur.DoesNotExist:
    print("✅ Aucun utilisateur existant")

# Test de création
try:
    form = UtilisateurCreationForm(data=test_data)
    
    if form.is_valid():
        print("✅ Formulaire valide")
        user = form.save()
        
        print(f"📋 Utilisateur créé:")
        print(f"   Email: {user.email}")
        print(f"   Prénom: '{user.prenom}'")
        print(f"   Nom: '{user.nom}'")
        print(f"   Rôle: {user.role_autorise}")
        
        print("\n🎯 À vérifier dans Keycloak Admin Console:")
        print(f"   First Name: {user.prenom}")
        print(f"   Last Name: {user.nom}")
        print(f"   Email: {user.email}")
        
    else:
        print("❌ Erreurs formulaire:", form.errors)
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("=== Fin du test ===")
