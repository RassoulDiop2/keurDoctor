#!/usr/bin/env python3
"""
Script pour créer une carte RFID de test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import RFIDCard, Utilisateur
from django.utils import timezone

def main():
    try:
        # Récupérer un utilisateur admin
        user = Utilisateur.objects.filter(role_autorise='admin').first()
        if not user:
            print('❌ Aucun utilisateur admin trouvé')
            return
        
        # Créer ou mettre à jour la carte RFID test
        card, created = RFIDCard.objects.get_or_create(
            card_uid='test123456',
            defaults={
                'utilisateur': user,
                'actif': True,
                'date_creation': timezone.now()
            }
        )
        
        if created:
            print(f'✅ Carte RFID test créée: {card.card_uid}')
        else:
            card.utilisateur = user
            card.actif = True
            card.save()
            print(f'✅ Carte RFID test mise à jour: {card.card_uid}')
        
        print(f'👤 Utilisateur: {user.prenom} {user.nom} ({user.email})')
        print(f'🎭 Rôle: {user.role_autorise}')
        print(f'🔓 Actif: {user.est_actif}')
        
    except Exception as e:
        print(f'❌ Erreur: {e}')

if __name__ == '__main__':
    main()
