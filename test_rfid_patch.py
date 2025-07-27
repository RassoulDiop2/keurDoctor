#!/usr/bin/env python3
"""
Test direct de l'API RFID avec le patch
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.rfid_arduino_handler import lire_uid_rfid
from comptes.models import RFIDCard, Utilisateur

def test_rfid_patch():
    print("=== TEST PATCH RFID ===")
    
    # Test 1: Function RFID
    print("1. Test fonction lire_uid_rfid()...")
    try:
        uid = lire_uid_rfid()
        print(f"   ✅ UID retourné: {uid}")
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return
    
    # Test 2: Vérifier carte en DB
    print("2. Vérification carte en base...")
    try:
        card = RFIDCard.objects.filter(card_uid=uid, actif=True).first()
        if card:
            print(f"   ✅ Carte trouvée: {card.card_uid}")
            print(f"   👤 Utilisateur: {card.utilisateur.prenom} {card.utilisateur.nom}")
            print(f"   📧 Email: {card.utilisateur.email}")
            print(f"   🎭 Rôle: {card.utilisateur.role_autorise}")
        else:
            print(f"   ❌ Carte {uid} non trouvée en base")
            # Créer la carte test
            print("   🔧 Création carte test...")
            user = Utilisateur.objects.filter(role_autorise='admin').first()
            if user:
                card = RFIDCard.objects.create(
                    card_uid=uid,
                    utilisateur=user,
                    actif=True
                )
                print(f"   ✅ Carte créée pour {user.email}")
            else:
                print("   ❌ Aucun utilisateur admin disponible")
    except Exception as e:
        print(f"   ❌ Erreur DB: {e}")

if __name__ == '__main__':
    test_rfid_patch()
