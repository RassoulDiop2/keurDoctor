from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from comptes.models import Utilisateur, Patient, RFIDCard
from django.utils import timezone
import uuid

User = get_user_model()

class Command(BaseCommand):
    help = 'Crée des utilisateurs de test avec des cartes RFID pour tester l\'authentification RFID + OTP'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprime tous les utilisateurs de test RFID existants',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des utilisateurs de test RFID...')
            Utilisateur.objects.filter(email__startswith='patient.rfid.test').delete()
            self.stdout.write(self.style.SUCCESS('Utilisateurs de test RFID supprimés.'))
            return

        # Créer des utilisateurs de test avec cartes RFID
        test_users = [
            {
                'email': 'patient.rfid.test1@keurdoctor.com',
                'prenom': 'Marie',
                'nom': 'Dupont',
                'role_autorise': 'patient',
                'card_uid': 'RFID001234567890',
                'date_naissance': '1985-03-15'
            },
            {
                'email': 'patient.rfid.test2@keurdoctor.com',
                'prenom': 'Jean',
                'nom': 'Martin',
                'role_autorise': 'patient',
                'card_uid': 'RFID009876543210',
                'date_naissance': '1978-07-22'
            },
            {
                'email': 'patient.rfid.test3@keurdoctor.com',
                'prenom': 'Sophie',
                'nom': 'Bernard',
                'role_autorise': 'patient',
                'card_uid': 'RFID005566778899',
                'date_naissance': '1992-11-08'
            }
        ]

        created_count = 0
        for user_data in test_users:
            try:
                # Créer l'utilisateur
                utilisateur = Utilisateur.objects.create_user(
                    email=user_data['email'],
                    prenom=user_data['prenom'],
                    nom=user_data['nom'],
                    password='Test123!',
                    role_autorise=user_data['role_autorise'],
                    est_actif=True
                )

                # Créer le profil patient
                from datetime import date
                patient = Patient.objects.create(
                    utilisateur=utilisateur,
                    date_naissance=date.fromisoformat(user_data['date_naissance']),
                    numero_dossier=f"P{utilisateur.id:06d}"
                )

                # Créer la carte RFID
                rfid_card = RFIDCard.objects.create(
                    utilisateur=utilisateur,
                    card_uid=user_data['card_uid'],
                    actif=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Utilisateur créé: {utilisateur.email} '
                        f'(Patient: {patient.numero_dossier}, RFID: {rfid_card.card_uid})'
                    )
                )
                created_count += 1

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Erreur lors de la création de {user_data["email"]}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 {created_count} utilisateurs de test RFID créés avec succès!')
        )
        
        self.stdout.write('\n📋 Informations de test:')
        self.stdout.write('   • Code OTP de test: 123456')
        self.stdout.write('   • URL de connexion RFID: /patient/rfid/login/')
        self.stdout.write('   • URL de test des méthodes: /authentification/methodes/')
        
        self.stdout.write('\n👥 Utilisateurs créés:')
        for user_data in test_users:
            self.stdout.write(f'   • {user_data["email"]} (RFID: {user_data["card_uid"]})')
        
        self.stdout.write('\n🔧 Pour supprimer les utilisateurs de test:')
        self.stdout.write('   python manage.py create_rfid_test_users --clear') 