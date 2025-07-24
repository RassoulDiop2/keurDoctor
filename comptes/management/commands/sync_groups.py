from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from comptes.models import Utilisateur
from comptes.views import sync_django_groups
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronise les groupes Django avec les rôles des utilisateurs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Créer les groupes de base s\'ils n\'existent pas',
        )
        parser.add_argument(
            '--sync-all',
            action='store_true',
            help='Synchroniser tous les utilisateurs avec leurs groupes',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Vérifier l\'état de synchronisation des groupes',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Démarrage de la synchronisation des groupes Django...')
        )

        if options['create_groups']:
            self.create_base_groups()

        if options['sync_all']:
            self.sync_all_users()

        if options['verify']:
            self.verify_synchronization()

        if not any([options['create_groups'], options['sync_all'], options['verify']]):
            # Par défaut, faire toutes les opérations
            self.create_base_groups()
            self.sync_all_users()
            self.verify_synchronization()

        self.stdout.write(
            self.style.SUCCESS('✅ Synchronisation terminée!')
        )

    def create_base_groups(self):
        """Créer les groupes de base"""
        self.stdout.write('📁 Création des groupes de base...')
        
        groups_to_create = ['administrateurs', 'medecins', 'patients']
        for group_name in groups_to_create:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✅ Groupe "{group_name}" créé')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ℹ️ Groupe "{group_name}" existe déjà')
                )

    def sync_all_users(self):
        """Synchroniser tous les utilisateurs avec leurs groupes"""
        self.stdout.write('🔄 Synchronisation des utilisateurs...')
        
        users_with_roles = Utilisateur.objects.filter(role_autorise__isnull=False)
        success_count = 0
        error_count = 0
        
        for user in users_with_roles:
            try:
                result = sync_django_groups(user, user.role_autorise)
                if result:
                    success_count += 1
                    user_groups = [g.name for g in user.groups.all()]
                    self.stdout.write(
                        f'  ✅ {user.email} (rôle: {user.role_autorise}) -> groupes: {user_groups}'
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ Erreur pour {user.email}')
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Exception pour {user.email}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'📊 Synchronisation: {success_count} succès, {error_count} erreurs')
        )

    def verify_synchronization(self):
        """Vérifier l'état de synchronisation"""
        self.stdout.write('🔍 Vérification de la synchronisation...')
        
        users_with_roles = Utilisateur.objects.filter(role_autorise__isnull=False)
        desynchronized = []
        
        group_mapping = {
            'admin': 'administrateurs',
            'medecin': 'medecins',
            'patient': 'patients'
        }
        
        for user in users_with_roles:
            role = user.role_autorise
            expected_group = group_mapping.get(role, role)
            
            try:
                group = Group.objects.get(name=expected_group)
                if not user.groups.filter(id=group.id).exists():
                    desynchronized.append({
                        'user': user.email,
                        'role': role,
                        'missing_group': expected_group,
                        'current_groups': [g.name for g in user.groups.all()]
                    })
            except Group.DoesNotExist:
                desynchronized.append({
                    'user': user.email,
                    'role': role,
                    'missing_group': f'{expected_group} (groupe inexistant)',
                    'current_groups': [g.name for g in user.groups.all()]
                })
        
        if desynchronized:
            self.stdout.write(
                self.style.WARNING(f'⚠️ {len(desynchronized)} utilisateurs désynchronisés:')
            )
            for item in desynchronized:
                self.stdout.write(
                    f'  👤 {item["user"]} (rôle: {item["role"]}) -> manque: {item["missing_group"]}, a: {item["current_groups"]}'
                )
        else:
            self.stdout.write(
                self.style.SUCCESS('✅ Tous les utilisateurs sont correctement synchronisés!')
            )
