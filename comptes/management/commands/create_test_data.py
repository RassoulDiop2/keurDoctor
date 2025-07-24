from django.core.management.base import BaseCommand
from comptes.models import Utilisateur, MedecinNew, PatientNew, RendezVous, SpecialiteMedicale
from django.contrib.auth.models import Group
from datetime import datetime, timedelta
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Crée des données de test pour le dashboard patient'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🏥 Création des données de test pour le dashboard patient...'))

        # 1. Créer des spécialités médicales
        specialites = [
            'Cardiologie', 'Dermatologie', 'Pédiatrie', 'Gynécologie', 
            'Neurologie', 'Orthopédie', 'Ophtalmologie', 'ORL'
        ]
        
        specialites_objs = []
        for nom in specialites:
            specialite, created = SpecialiteMedicale.objects.get_or_create(
                nom=nom,
                defaults={'description': f'Spécialité médicale: {nom}'}
            )
            specialites_objs.append(specialite)
            if created:
                self.stdout.write(f'  ✅ Spécialité créée: {nom}')

        # 2. Créer des médecins de test
        medecins_data = [
            {'nom': 'Ndiaye', 'prenom': 'Aminata', 'email': 'dr.ndiaye@keurdoctor.com', 'specialite': 'Cardiologie'},
            {'nom': 'Ba', 'prenom': 'Mamadou', 'email': 'dr.ba@keurdoctor.com', 'specialite': 'Dermatologie'},
            {'nom': 'Sarr', 'prenom': 'Fatou', 'email': 'dr.sarr@keurdoctor.com', 'specialite': 'Pédiatrie'},
            {'nom': 'Diallo', 'prenom': 'Omar', 'email': 'dr.diallo@keurdoctor.com', 'specialite': 'Neurologie'},
            {'nom': 'Fall', 'prenom': 'Awa', 'email': 'dr.fall@keurdoctor.com', 'specialite': 'Gynécologie'},
        ]

        medecins_crees = []
        for data in medecins_data:
            # Créer l'utilisateur médecin s'il n'existe pas
            utilisateur, created = Utilisateur.objects.get_or_create(
                email=data['email'],
                defaults={
                    'prenom': data['prenom'],
                    'nom': data['nom'],
                    'role_autorise': 'medecin',
                    'is_active': True
                }
            )
            
            if created:
                self.stdout.write(f'  👤 Utilisateur médecin créé: {data["prenom"]} {data["nom"]}')
                
                # Ajouter au groupe medecins
                try:
                    group_medecins = Group.objects.get(name='medecins')
                    utilisateur.groups.add(group_medecins)
                except Group.DoesNotExist:
                    self.stdout.write(self.style.WARNING('  ⚠️ Groupe "medecins" non trouvé'))

            # Créer le profil médecin
            medecin, created = MedecinNew.objects.get_or_create(
                utilisateur=utilisateur,
                defaults={
                    'numero_ordre': f'MD{random.randint(1000, 9999)}',
                }
            )
            
            if created:
                # Ajouter la spécialité
                try:
                    specialite = SpecialiteMedicale.objects.get(nom=data['specialite'])
                    medecin.specialites.add(specialite)
                    self.stdout.write(f'  🏥 Médecin créé: Dr. {data["prenom"]} {data["nom"]} ({data["specialite"]})')
                except SpecialiteMedicale.DoesNotExist:
                    self.stdout.write(f'  ⚠️ Spécialité {data["specialite"]} non trouvée')
            
            medecins_crees.append(medecin)

        # 3. Créer des rendez-vous de test si on a des patients
        patients = PatientNew.objects.all()
        if patients.exists() and medecins_crees:
            self.stdout.write('📅 Création de rendez-vous de test...')
            
            # Pour chaque patient, créer quelques rendez-vous
            for patient in patients[:3]:  # Limiter aux 3 premiers patients
                for i in range(random.randint(2, 5)):
                    medecin = random.choice(medecins_crees)
                    
                    # Dates variées (passées et futures)
                    if i % 3 == 0:  # Rendez-vous passés
                        date_rdv = timezone.now() - timedelta(days=random.randint(1, 60))
                        statut = 'TERMINE'
                    elif i % 3 == 1:  # Rendez-vous à venir
                        date_rdv = timezone.now() + timedelta(days=random.randint(1, 30))
                        statut = random.choice(['EN_ATTENTE', 'CONFIRME'])
                    else:  # Rendez-vous annulés
                        date_rdv = timezone.now() - timedelta(days=random.randint(1, 30))
                        statut = 'ANNULE'
                    
                    # Heures de consultation normales
                    heure = random.choice([8, 9, 10, 11, 14, 15, 16, 17])
                    minute = random.choice([0, 30])
                    date_rdv = date_rdv.replace(hour=heure, minute=minute, second=0, microsecond=0)
                    
                    motifs = [
                        'Consultation de contrôle',
                        'Douleurs abdominales',
                        'Suivi médical',
                        'Examen de routine',
                        'Problème dermatologique',
                        'Consultation cardiaque',
                        'Bilan de santé'
                    ]
                    
                    rdv, created = RendezVous.objects.get_or_create(
                        patient=patient,
                        medecin=medecin,
                        date_rdv=date_rdv,
                        defaults={
                            'motif': random.choice(motifs),
                            'statut': statut
                        }
                    )
                    
                    if created:
                        self.stdout.write(
                            f'  📅 RDV créé: {patient.utilisateur.prenom} → Dr. {medecin.utilisateur.nom} '
                            f'({date_rdv.strftime("%d/%m/%Y %H:%M")}) - {statut}'
                        )

        self.stdout.write(self.style.SUCCESS('\n✅ Données de test créées avec succès !'))
        self.stdout.write(self.style.SUCCESS('🔗 Vous pouvez maintenant tester le dashboard patient sur http://localhost:3000/patient/'))
