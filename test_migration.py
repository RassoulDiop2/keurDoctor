#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import *
from django.contrib.auth.models import Group

# Vérifier que les modèles fonctionnent
print("Test des nouveaux modèles :")
print("============================")

# Test des spécialités médicales
print("1. Création de spécialités médicales...")
specialites = [
    "Cardiologie",
    "Dermatologie", 
    "Pédiatrie",
    "Gynécologie",
    "Médecine générale"
]

created_count = 0
for nom in specialites:
    spec, created = SpecialiteMedicale.objects.get_or_create(
        nom=nom,
        defaults={'description': f'Spécialité en {nom.lower()}'}
    )
    if created:
        created_count += 1
        print(f"   ✅ Créé: {spec}")
    else:
        print(f"   ℹ️  Existe: {spec}")

print(f"   Total spécialités: {SpecialiteMedicale.objects.count()}")

# Test des comptes utilisateurs
print("\n2. Vérification des utilisateurs...")
print(f"   Total utilisateurs: {Utilisateur.objects.count()}")
print(f"   Total médecins: {Medecin.objects.count()}")  
print(f"   Total patients: {Patient.objects.count()}")

# Test des nouvelles tables
print("\n3. Vérification des nouvelles tables...")
print(f"   Consultations: {Consultation.objects.count()}")
print(f"   Prescriptions: {Prescription.objects.count()}")
print(f"   Documents médicaux: {DocumentMedical.objects.count()}")

print("\n✅ Tous les modèles fonctionnent correctement !")
print("\n🎉 Migration terminée avec succès !")
print("\nLes tables suivantes sont maintenant disponibles pour les dashboards :")
print("- Gestion des consultations")
print("- Gestion des prescriptions") 
print("- Gestion des documents médicaux")
print("- Gestion des spécialités médicales")
print("- Nouveaux profils médecins et patients")
