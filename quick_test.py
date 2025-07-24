import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur, MedecinNew, PatientNew, SpecialiteMedicale
from datetime import date

print("🧪 Test rapide de création d'utilisateurs...")

# Test médecin
try:
    print("Création d'un médecin...")
    user = Utilisateur.objects.create_user(
        email="test.medecin@test.com",
        prenom="Dr",
        nom="Test",
        password="testpass123"
    )
    
    medecin = MedecinNew.objects.create(
        utilisateur=user,
        numero_ordre="TEST123"
    )
    
    print("✅ Médecin créé avec succès!")
    
    # Test ajout spécialité
    specialite, created = SpecialiteMedicale.objects.get_or_create(
        nom="Cardiologie",
        defaults={'description': 'Spécialité: Cardiologie'}
    )
    medecin.specialites.add(specialite)
    print("✅ Spécialité ajoutée!")
    
except Exception as e:
    print(f"❌ Erreur médecin: {e}")

# Test patient
try:
    print("\nCréation d'un patient...")
    user2 = Utilisateur.objects.create_user(
        email="test.patient@test.com",
        prenom="Patient",
        nom="Test",
        password="testpass123"
    )
    
    patient = PatientNew.objects.create(
        utilisateur=user2,
        numero_securite_sociale="123456789012345",
        date_naissance=date(1990, 1, 1)
    )
    
    print("✅ Patient créé avec succès!")
    
except Exception as e:
    print(f"❌ Erreur patient: {e}")

# Nettoyage
try:
    Utilisateur.objects.filter(email__contains="@test.com").delete()
    print("\n🧹 Données de test nettoyées")
except:
    pass

print("\n🎉 Test terminé!")
