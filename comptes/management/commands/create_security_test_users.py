from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction
from comptes.models import Utilisateur, Medecin, Patient, Administrateur

class Command(BaseCommand):
    help = 'Crée des utilisateurs de test pour les tests de sécurité'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la recréation des utilisateurs existants',
        )

    def handle(self, *args, **options):
        # Données des utilisateurs de test pour la sécurité
        test_users = [
            {
                'email': 'patient.test@keurdoctor.com',
                'password': 'Patient123!',
                'prenom': 'Patient',
                'nom': 'Test',
                'role_autorise': 'patient',
                'role_demande': 'patient',
                'est_actif': True,
            },
            {
                'email': 'medecin.test@keurdoctor.com',
                'password': 'Medecin123!',
                'prenom': 'Médecin',
                'nom': 'Test',
                'role_autorise': 'medecin',
                'role_demande': 'medecin',
                'est_actif': True,
            },
            {
                'email': 'admin.test@keurdoctor.com',
                'password': 'Admin123!',
                'prenom': 'Admin',
                'nom': 'Test',
                'role_autorise': 'admin',
                'role_demande': 'admin',
                'est_actif': True,
            },
            {
                'email': 'patient.malveillant@keurdoctor.com',
                'password': 'Hack123!',
                'prenom': 'Patient',
                'nom': 'Malveillant',
                'role_autorise': 'patient',
                'role_demande': 'patient',
                'est_actif': True,
            }
        ]

        # Créer les utilisateurs
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for user_data in test_users:
                email = user_data['email']
                
                # Vérifier si l'utilisateur existe
                user_exists = Utilisateur.objects.filter(email=email).exists()
                
                if user_exists and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(f"Utilisateur '{email}' existe déjà. Utilisez --force pour le recréer.")
                    )
                    continue
                
                # Supprimer l'utilisateur existant si --force
                if user_exists and options['force']:
                    Utilisateur.objects.filter(email=email).delete()
                    updated_count += 1
                    self.stdout.write(f"Utilisateur '{email}' supprimé et sera recréé.")
                
                # Créer l'utilisateur
                user = Utilisateur.objects.create_user(
                    email=user_data['email'],
                    password=user_data['password'],
                    prenom=user_data['prenom'],
                    nom=user_data['nom'],
                    role_autorise=user_data['role_autorise'],
                    role_demande=user_data['role_demande'],
                    est_actif=user_data['est_actif']
                )
                
                # Créer le profil spécifique selon le rôle
                if user_data['role_autorise'] == 'medecin':
                    Medecin.objects.create(
                        utilisateur=user,
                        specialite='Médecine générale',
                        numero_praticien=f"MED{user.id:04d}"
                    )
                elif user_data['role_autorise'] == 'patient':
                    Patient.objects.create(
                        utilisateur=user,
                        date_naissance='1990-01-01',
                        numero_dossier=f"PAT{user.id:04d}"
                    )
                elif user_data['role_autorise'] == 'admin':
                    Administrateur.objects.create(
                        utilisateur=user,
                        niveau_acces=1
                    )
                
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Utilisateur '{email}' créé avec le rôle '{user_data['role_autorise']}'"
                    )
                )

        # Résumé
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"🎉 Création terminée!"))
        self.stdout.write(f"Utilisateurs créés: {created_count}")
        if updated_count > 0:
            self.stdout.write(f"Utilisateurs mis à jour: {updated_count}")
        
        self.stdout.write("\n📋 Comptes de test pour la sécurité:")
        self.stdout.write("| Rôle | Email | Mot de passe | Description |")
        self.stdout.write("|------|-------|--------------|-------------|")
        for user_data in test_users:
            role = user_data['role_autorise']
            email = user_data['email']
            password = user_data['password']
            description = "Utilisateur normal" if "malveillant" not in email else "Utilisateur pour test d'intrusion"
            self.stdout.write(f"| {role} | {email} | {password} | {description} |")
        
        self.stdout.write(f"\n🧪 Tests de sécurité à effectuer:")
        self.stdout.write(f"1. Connectez-vous avec patient.test@keurdoctor.com")
        self.stdout.write(f"2. Essayez d'accéder à /medecin/ → Doit être refusé")
        self.stdout.write(f"3. Essayez d'accéder à /admin/ → Doit être refusé")
        self.stdout.write(f"4. Connectez-vous avec medecin.test@keurdoctor.com")
        self.stdout.write(f"5. Accédez à /medecin/ → Doit fonctionner")
        self.stdout.write(f"6. Essayez d'accéder à /admin/ → Doit être refusé")
        self.stdout.write(f"7. Connectez-vous avec admin.test@keurdoctor.com")
        self.stdout.write(f"8. Accédez à /admin/ → Doit fonctionner")
        
        self.stdout.write(f"\n🌐 Accès: http://localhost:8000") 