from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Initialise les groupes Django pour la synchronisation avec Keycloak'

    def handle(self, *args, **options):
        """Crée les groupes Django standards"""
        
        # Définir les groupes et leurs permissions
        groups_config = {
            'admin': {
                'description': 'Administrateurs système',
                'permissions': ['add_user', 'change_user', 'delete_user', 'view_user']
            },
            'medecin': {
                'description': 'Médecins',
                'permissions': ['view_user', 'change_user']
            },
            'patient': {
                'description': 'Patients',
                'permissions': ['view_user']
            }
        }
        
        created_count = 0
        updated_count = 0
        
        for group_name, config in groups_config.items():
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Groupe "{group_name}" créé')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Groupe "{group_name}" existe déjà')
                )
            
            # Ajouter les permissions de base
            user_content_type = ContentType.objects.get_for_model(
                Group.objects.get(name=group_name).user_set.model
            )
            
            for perm_codename in config['permissions']:
                try:
                    permission = Permission.objects.get(
                        codename=perm_codename,
                        content_type=user_content_type
                    )
                    group.permissions.add(permission)
                except Permission.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f'Permission "{perm_codename}" non trouvée')
                    )
        
        # Résumé
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Groupes créés: {created_count}')
        self.stdout.write(f'Groupes existants: {updated_count}')
        self.stdout.write('='*50)
        
        # Afficher les groupes existants
        self.stdout.write('\nGroupes Django disponibles:')
        for group in Group.objects.all():
            permissions = [p.codename for p in group.permissions.all()]
            self.stdout.write(f'  - {group.name} (permissions: {", ".join(permissions)})')
        
        self.stdout.write('\n' + self.style.SUCCESS('Initialisation des groupes terminée'))
