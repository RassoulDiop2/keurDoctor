"""
Script de gestion des utilisateurs et cartes RFID de test pour les médecins
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from comptes.models import Utilisateur, RFIDCard, MedecinNew
from datetime import date


class Command(BaseCommand):
    help = 'Crée des utilisateurs médecins de test avec cartes RFID'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Supprimer les utilisateurs médecins de test existants',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Suppression des médecins de test RFID...')
            Utilisateur.objects.filter(email__startswith='medecin.rfid.test').delete()
            self.stdout.write(self.style.SUCCESS('Médecins de test RFID supprimés.'))
            return

        # Créer des médecins de test avec cartes RFID
        test_medecins = [
            {
                'email': 'medecin.rfid.test1@keurdoctor.com',
                'prenom': 'Dr. Jean',
                'nom': 'Dupont',
                'role_autorise': 'medecin',
                'card_uid': 'MEDECIN_RFID_001',
                'numero_ordre': 'MED001',
                'specialite': 'Médecine générale'
            },
            {
                'email': 'medecin.rfid.test2@keurdoctor.com',
                'prenom': 'Dr. Marie',
                'nom': 'Martin',
                'role_autorise': 'medecin',
                'card_uid': 'MEDECIN_RFID_002',
                'numero_ordre': 'MED002',
                'specialite': 'Cardiologie'
            },
            {
                'email': 'medecin.rfid.test3@keurdoctor.com',
                'prenom': 'Dr. Paul',
                'nom': 'Bernard',
                'role_autorise': 'medecin',
                'card_uid': 'MEDECIN_RFID_003',
                'numero_ordre': 'MED003',
                'specialite': 'Dermatologie'
            },
        ]

        for medecin_data in test_medecins:
            try:
                # Vérifier si l'utilisateur existe déjà
                if Utilisateur.objects.filter(email=medecin_data['email']).exists():
                    self.stdout.write(
                        self.style.WARNING(f"Médecin {medecin_data['email']} existe déjà.")
                    )
                    continue

                # Créer l'utilisateur médecin
                utilisateur = Utilisateur.objects.create(
                    email=medecin_data['email'],
                    prenom=medecin_data['prenom'],
                    nom=medecin_data['nom'],
                    password=make_password('medecin123'),  # Mot de passe de test
                    role_autorise=medecin_data['role_autorise'],
                    est_actif=True
                )

                # Créer le profil médecin
                profil_medecin = MedecinNew.objects.create(
                    utilisateur=utilisateur,
                    numero_ordre=medecin_data['numero_ordre'],
                    telephone_cabinet='0123456789',
                    adresse_cabinet='123 Rue de la Santé, Paris',
                    horaires_consultation='Lundi-Vendredi 9h-17h',
                    tarif_consultation=60.00,
                    accepte_nouveaux_patients=True,
                    date_installation=date.today()
                )

                # Créer la carte RFID
                rfid_card = RFIDCard.objects.create(
                    utilisateur=utilisateur,
                    card_uid=medecin_data['card_uid'],
                    actif=True
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Médecin créé: {medecin_data['email']} "
                        f"(RFID: {medecin_data['card_uid']})"
                    )
                )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Erreur lors de la création de {medecin_data['email']}: {e}"
                    )
                )

        self.stdout.write(self.style.SUCCESS('\n🎉 Médecins de test créés avec succès !'))
        self.stdout.write('\n📋 Informations de connexion:')
        self.stdout.write('┌─────────────────────────────────────────────────────────────┐')
        self.stdout.write('│ AUTHENTIFICATION CLASSIQUE (Username + MDP + OTP)          │')
        self.stdout.write('├─────────────────────────────────────────────────────────────┤')
        for medecin in test_medecins:
            self.stdout.write(f'│ Email: {medecin["email"]:<35} │')
            self.stdout.write(f'│ MDP: medecin123{" " * 42} │')
        self.stdout.write('├─────────────────────────────────────────────────────────────┤')
        self.stdout.write('│ AUTHENTIFICATION RFID (Carte RFID + OTP)                   │')
        self.stdout.write('├─────────────────────────────────────────────────────────────┤')
        for medecin in test_medecins:
            self.stdout.write(f'│ Email: {medecin["email"]:<35} │')
            self.stdout.write(f'│ RFID: {medecin["card_uid"]:<36} │')
        self.stdout.write('├─────────────────────────────────────────────────────────────┤')
        self.stdout.write('│ CODE OTP DE TEST: 123456                                   │')
        self.stdout.write('└─────────────────────────────────────────────────────────────┘')
        
        self.stdout.write('\n🔗 URLs de test:')
        self.stdout.write('• Connexion RFID médecin: http://127.0.0.1:8000/medecin/rfid/login/')
        self.stdout.write('• Dashboard médecin: http://127.0.0.1:8000/medecin/')
        self.stdout.write('• Gestion RFID admin: http://127.0.0.1:8000/rfid/enregistrer/')
