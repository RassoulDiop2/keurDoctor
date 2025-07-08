from django.core.management.base import BaseCommand
from django.conf import settings
from comptes.models import Utilisateur
from comptes.views import sync_role_to_keycloak
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Synchronise tous les rôles Django vers Keycloak'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait fait sans effectuer les modifications',
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Synchronise uniquement l\'utilisateur avec cet email',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la synchronisation même en cas d\'erreur',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_email = options['user_email']
        force = options['force']

        self.stdout.write(
            self.style.SUCCESS('🔄 Début de la synchronisation des rôles Django vers Keycloak')
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('⚠️  Mode DRY-RUN activé - Aucune modification ne sera effectuée')
            )

        # Filtrer les utilisateurs
        if user_email:
            users = Utilisateur.objects.filter(email=user_email)
            if not users.exists():
                self.stdout.write(
                    self.style.ERROR(f'❌ Utilisateur avec l\'email {user_email} non trouvé')
                )
                return
        else:
            users = Utilisateur.objects.filter(role_autorise__isnull=False)

        total_users = users.count()
        success_count = 0
        error_count = 0

        self.stdout.write(f'📊 {total_users} utilisateur(s) à synchroniser')

        for i, user in enumerate(users, 1):
            self.stdout.write(f'\n[{i}/{total_users}] Traitement de {user.email}...')
            
            if dry_run:
                self.stdout.write(
                    f'   🔍 Rôle actuel: {user.role_autorise or "Aucun"}'
                )
                continue

            try:
                # Synchroniser le rôle
                success = sync_role_to_keycloak(user, user.role_autorise)
                
                if success:
                    self.stdout.write(
                        self.style.SUCCESS(f'   ✅ Synchronisation réussie pour {user.email} (rôle: {user.role_autorise})')
                    )
                    success_count += 1
                else:
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Échec de synchronisation pour {user.email}')
                    )
                    error_count += 1
                    
                    if not force:
                        self.stdout.write(
                            self.style.WARNING('   ⚠️  Arrêt en cas d\'erreur (utilisez --force pour continuer)')
                        )
                        break

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'   💥 Erreur lors de la synchronisation de {user.email}: {e}')
                )
                error_count += 1
                
                if not force:
                    self.stdout.write(
                        self.style.WARNING('   ⚠️  Arrêt en cas d\'erreur (utilisez --force pour continuer)')
                    )
                    break

        # Résumé final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('📋 RÉSUMÉ DE LA SYNCHRONISATION'))
        self.stdout.write('='*50)
        
        if dry_run:
            self.stdout.write(f'🔍 Mode DRY-RUN: {total_users} utilisateur(s) auraient été traités')
        else:
            self.stdout.write(f'✅ Succès: {success_count}')
            self.stdout.write(f'❌ Erreurs: {error_count}')
            self.stdout.write(f'📊 Total traité: {success_count + error_count}/{total_users}')
            
            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS('🎉 Toutes les synchronisations ont réussi !')
                )
            elif success_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  {error_count} erreur(s) sur {total_users} utilisateur(s)')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('💥 Aucune synchronisation n\'a réussi')
                )

        # Conseils en cas d'erreur
        if error_count > 0 and not dry_run:
            self.stdout.write('\n💡 CONSEILS EN CAS D\'ERREUR:')
            self.stdout.write('   1. Vérifiez que Keycloak est démarré et accessible')
            self.stdout.write('   2. Vérifiez les credentials admin dans settings.py')
            self.stdout.write('   3. Vérifiez que les rôles existent dans Keycloak')
            self.stdout.write('   4. Utilisez --force pour continuer malgré les erreurs')
            self.stdout.write('   5. Consultez les logs Django pour plus de détails') 