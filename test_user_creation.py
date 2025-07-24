#!/usr/bin/env python
import os
import sys
import django

# Configuration Django
sys.path.append(r'h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

# Test des modèles
from comptes.models import Utilisateur, MedecinNew, PatientNew

print("Test de création d'utilisateur...")

try:
    # Test de création d'un médecin
    user = Utilisateur.objects.create_user(
        email='test.medecin@example.com',
        prenom='Test',
        nom='Medecin',
        password='test123',
        role_autorise='medecin'
    )
    
    medecin = MedecinNew.objects.create(
        utilisateur=user,
        numero_ordre='12345'
    )
    
    print('✅ Création d\'utilisateur médecin réussie!')
    print(f'Utilisateur: {user.email}')
    print(f'Médecin: {medecin}')
    
    # Nettoyage
    medecin.delete()
    user.delete()
    
except Exception as e:
    print(f'❌ Erreur: {e}')
    import traceback
    traceback.print_exc()
