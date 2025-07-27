#!/usr/bin/env python
"""
Script de test pour le système RFID médecin
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur, MedecinNew, RFIDCard
from django.contrib.auth.hashers import make_password

def create_test_medecin():
    """Créer un médecin de test avec carte RFID"""
    print("=== Création d'un médecin de test ===")
    
    # Créer l'utilisateur
    username = "dr_test"
    if Utilisateur.objects.filter(username=username).exists():
        print(f"L'utilisateur {username} existe déjà")
        user = Utilisateur.objects.get(username=username)
    else:
        user = Utilisateur.objects.create(
            username=username,
            email="dr.test@keurdoctor.com",
            password=make_password("test123"),
            role="medecin",
            nom="Test",
            prenom="Docteur",
            numero_telephone="77123456789",
            is_staff=True,
            is_active=True
        )
        print(f"Utilisateur {username} créé")
    
    # Créer le profil médecin
    if MedecinNew.objects.filter(utilisateur=user).exists():
        print("Profil médecin existe déjà")
        medecin = MedecinNew.objects.get(utilisateur=user)
    else:
        medecin = MedecinNew.objects.create(
            utilisateur=user,
            specialite="Généraliste",
            numero_ordre="12345"
        )
        print("Profil médecin créé")
    
    # Créer la carte RFID
    card_uid = "A1B2C3D4"
    if RFIDCard.objects.filter(card_uid=card_uid).exists():
        print(f"Carte RFID {card_uid} existe déjà")
    else:
        rfid_card = RFIDCard.objects.create(
            card_uid=card_uid,
            user=user,
            is_active=True
        )
        print(f"Carte RFID {card_uid} créée pour {username}")
    
    print("\n=== Résumé ===")
    print(f"Username: {user.username}")
    print(f"Email: {user.email}")
    print(f"Mot de passe: test123")
    print(f"Carte RFID: {card_uid}")
    print(f"Rôle: {user.role}")

def test_medecin_data():
    """Afficher les données des médecins"""
    print("\n=== Médecins existants ===")
    medecins = MedecinNew.objects.all()
    if not medecins:
        print("Aucun médecin trouvé")
    else:
        for medecin in medecins:
            print(f"- {medecin.utilisateur.username} ({medecin.utilisateur.email})")
            print(f"  Spécialité: {medecin.specialite}")
            print(f"  N° ordre: {medecin.numero_ordre}")
    
    print("\n=== Cartes RFID médecins ===")
    cards = RFIDCard.objects.filter(user__role='medecin')
    if not cards:
        print("Aucune carte RFID médecin trouvée")
    else:
        for card in cards:
            print(f"- {card.card_uid}: {card.user.username} ({'Actif' if card.is_active else 'Inactif'})")

if __name__ == "__main__":
    try:
        create_test_medecin()
        test_medecin_data()
        print("\n✅ Test terminé avec succès!")
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
