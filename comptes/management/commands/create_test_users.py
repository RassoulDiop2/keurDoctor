from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group
from django.db import transaction


class Command(BaseCommand):
    help = 'Crée les utilisateurs de test automatiquement'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la recréation des utilisateurs existants',
        )

    def handle(self, *args, **options):
        # Données des utilisateurs de test
        # ⚠️ IMPORTANT: Si vous modifiez ces mots de passe, 
        # mettez aussi à jour sync_users_to_keycloak.py méthode get_user_password()
        test_users = [
            {
                'username': 'admin',
                'password': 'Admin123!',
                'email': 'admin@keurdoctor.com',
                'first_name': 'Admin',
                'last_name': 'Système',
                'group': 'admin',
                'is_superuser': False,
                'is_staff': False,
            },
            {
                'username': 'abdoulaye',
                'password': 'laye123!',
                'email': 'dr.laye@keurdoctor.com',
                'first_name': 'Abdoulaye',
                'last_name': 'Laye',
                'group': 'medecin',
                'is_superuser': False,
                'is_staff': False
            },
            {
                'username': 'test',
                'password': 'Test123!',
                'email': 'patient@test.com',
                'first_name': 'Patient',
                'last_name': 'Test',
                'group': 'patient',
                'is_superuser': False,
                'is_staff': False
            }
        ]

        # Vérifier que les groupes existent
        required_groups = ['admin', 'medecin', 'patient']
        missing_groups = []
        
        for group_name in required_groups:
            try:
                Group.objects.get(name=group_name)
            except Group.DoesNotExist:
                missing_groups.append(group_name)
        
        if missing_groups:
            self.stdout.write(
                self.style.ERROR(
                    f"Groupes manquants: {', '.join(missing_groups)}. "
                    "Exécutez d'abord 'python manage.py init_groups'"
                )
            )
            return

        # Créer les utilisateurs
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for user_data in test_users:
                username = user_data['username']
                group_name = user_data['group']
                
                # Vérifier si l'utilisateur existe
                user_exists = User.objects.filter(username=username).exists()
                
                if user_exists and not options['force']:
                    self.stdout.write(
                        self.style.WARNING(f"Utilisateur '{username}' existe déjà. Utilisez --force pour le recréer.")
                    )
                    continue
                
                # Supprimer l'utilisateur existant si --force
                if user_exists and options['force']:
                    User.objects.filter(username=username).delete()
                    updated_count += 1
                    self.stdout.write(f"Utilisateur '{username}' supprimé et sera recréé.")
                
                # Créer l'utilisateur
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name']
                )
                
                # Définir les permissions
                user.is_superuser = user_data['is_superuser']
                user.is_staff = user_data['is_staff']
                user.save()
                
                # Assigner le groupe
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
                
                created_count += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Utilisateur '{username}' créé avec le rôle '{group_name}'"
                    )
                )

        # Résumé
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"🎉 Création terminée!"))
        self.stdout.write(f"Utilisateurs créés: {created_count}")
        if updated_count > 0:
            self.stdout.write(f"Utilisateurs mis à jour: {updated_count}")
        
        self.stdout.write("\n📋 Comptes de test disponibles:")
        self.stdout.write("| Utilisateur | Mot de passe | Rôle | Email |")
        self.stdout.write("|-------------|--------------|------|-------|")
        for user_data in test_users:
            self.stdout.write(
                f"| {user_data['username']} | {user_data['password']} | "
                f"{user_data['group']} | {user_data['email']} |"
            )
        
        self.stdout.write(f"\n🌐 Accès: http://localhost:8000")
        self.stdout.write(f"🔧 Admin Django: http://localhost:8000/admin")
