import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from comptes.admin import UtilisateurCreationForm

# Test simple
print("=== Test de création utilisateur avec Keycloak ===")

test_data = {
    'email': 'test@example.com',
    'prenom': 'Jean',
    'nom': 'Dupont', 
    'role': 'medecin',
    'password1': 'TestPass123!',
    'password2': 'TestPass123!'
}

# Supprimer si existe
try:
    Utilisateur.objects.get(email=test_data['email']).delete()
    print("Utilisateur existant supprimé")
except:
    pass

# Créer
form = UtilisateurCreationForm(data=test_data)
if form.is_valid():
    user = form.save()
    print(f"✅ Utilisateur créé: {user.email}")
    print(f"   Prénom: {user.prenom}")
    print(f"   Nom: {user.nom}")
    print(f"   Rôle: {user.role_autorise}")
else:
    print("❌ Erreurs:", form.errors)

print("=== Fin du test ===")
