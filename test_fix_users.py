#!/usr/bin/env python
"""
Script de test pour vérifier la création d'utilisateurs avec les nouveaux modèles
"""
import os
import sys
import django
from datetime import date

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur, MedecinNew, PatientNew, SpecialiteMedicale

def test_medecin_creation():
    """Test de création d'un médecin"""
    print("🧪 Test de création d'un médecin...")
    
    try:
        # Créer l'utilisateur base
        utilisateur = Utilisateur.objects.create_user(
            email="test.medecin@test.com",
            prenom="Dr. Test",
            nom="Médecin",
            password="testpass123",
            role_autorise="medecin"
        )
        print(f"✅ Utilisateur créé: {utilisateur}")
        
        # Créer le profil médecin
        medecin = MedecinNew.objects.create(
            utilisateur=utilisateur,
            numero_ordre="TEST123",
            telephone_cabinet="0123456789",
            adresse_cabinet="Cabinet de test",
            tarif_consultation=50.00,
            accepte_nouveaux_patients=True,
            date_installation=date.today()
        )
        print(f"✅ Profil médecin créé: {medecin}")
        
        # Ajouter une spécialité si elle existe
        specialite = SpecialiteMedicale.objects.first()
        if specialite:
            medecin.specialites.add(specialite)
            print(f"✅ Spécialité ajoutée: {specialite}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du médecin: {e}")
        return False

def test_patient_creation():
    """Test de création d'un patient"""
    print("\n🧪 Test de création d'un patient...")
    
    try:
        # Créer l'utilisateur base
        utilisateur = Utilisateur.objects.create_user(
            email="test.patient@test.com",
            prenom="Patient",
            nom="Test",
            password="testpass123",
            role_autorise="patient"
        )
        print(f"✅ Utilisateur créé: {utilisateur}")
        
        # Créer le profil patient
        patient = PatientNew.objects.create(
            utilisateur=utilisateur,
            numero_securite_sociale="123456789012345",
            date_naissance=date(1990, 1, 1),
            telephone="0123456789",
            adresse="Adresse de test",
            groupe_sanguin="O+",
            allergies_connues="Aucune allergie connue",
            antecedents_medicaux="Aucun antécédent"
        )
        print(f"✅ Profil patient créé: {patient}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du patient: {e}")
        return False

def cleanup_test_data():
    """Nettoyer les données de test"""
    print("\n🧹 Nettoyage des données de test...")
    
    try:
        # Supprimer les utilisateurs de test
        test_users = Utilisateur.objects.filter(email__contains="@test.com")
        count = test_users.count()
        test_users.delete()
        print(f"✅ {count} utilisateurs de test supprimés")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")

if __name__ == "__main__":
    print("🚀 Test de création d'utilisateurs avec nouveaux modèles")
    print("=" * 60)
    
    # Tester la création d'un médecin
    medecin_ok = test_medecin_creation()
    
    # Tester la création d'un patient
    patient_ok = test_patient_creation()
    
    # Résumé
    print("\n📊 Résumé des tests:")
    print(f"   Médecin: {'✅ OK' if medecin_ok else '❌ ÉCHEC'}")
    print(f"   Patient: {'✅ OK' if patient_ok else '❌ ÉCHEC'}")
    
    if medecin_ok and patient_ok:
        print("\n🎉 Tous les tests sont passés ! La création d'utilisateurs fonctionne.")
    else:
        print("\n⚠️  Des problèmes ont été détectés dans la création d'utilisateurs.")
    
    # Nettoyer
    cleanup_test_data()
    print("\n✨ Tests terminés.")
