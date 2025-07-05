from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection


class Command(BaseCommand):
    help = 'Initialise complètement la base de données avec groupes et utilisateurs de test'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Remet à zéro la base de données complètement',
        )
        parser.add_argument(
            '--force-users',
            action='store_true',
            help='Force la recréation des utilisateurs existants',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🚀 Initialisation complète de KeurDoctor"))
        self.stdout.write("="*60)

        # Reset de la base si demandé
        if options['reset']:
            self.stdout.write(self.style.WARNING("⚠️  Reset de la base de données..."))
            
            # Supprimer la base SQLite
            import os
            db_path = 'db.sqlite3'
            if os.path.exists(db_path):
                os.remove(db_path)
                self.stdout.write("✅ Base de données supprimée")
            
            # Recréer les migrations
            self.stdout.write("🔄 Application des migrations...")
            call_command('migrate', verbosity=0)
            self.stdout.write("✅ Migrations appliquées")

        # 1. Créer les groupes
        self.stdout.write("\n📊 Étape 1: Création des groupes...")
        try:
            call_command('init_groups', verbosity=0)
            self.stdout.write("✅ Groupes créés (admin, medecin, patient)")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la création des groupes: {e}"))
            return

        # 2. Créer les utilisateurs de test
        self.stdout.write("\n👥 Étape 2: Création des utilisateurs de test...")
        try:
            if options['force_users']:
                call_command('create_test_users', force=True, verbosity=0)
            else:
                call_command('create_test_users', verbosity=0)
            self.stdout.write("✅ Utilisateurs de test créés")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Erreur lors de la création des utilisateurs: {e}"))
            return

        # 3. Vérification finale
        self.stdout.write("\n🔍 Étape 3: Vérification...")
        from django.contrib.auth.models import User, Group
        
        users_count = User.objects.count()
        groups_count = Group.objects.count()
        
        self.stdout.write(f"👥 Utilisateurs: {users_count}")
        self.stdout.write(f"📊 Groupes: {groups_count}")

        # Afficher les utilisateurs créés
        self.stdout.write("\n📋 Utilisateurs disponibles:")
        for user in User.objects.all():
            groups = [g.name for g in user.groups.all()]
            status = "superuser" if user.is_superuser else "utilisateur"
            self.stdout.write(f"  • {user.username} ({status}) - Groupes: {groups}")

        # Instructions finales
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS("🎉 Initialisation terminée avec succès!"))
        self.stdout.write("\n🌐 Étapes suivantes:")
        self.stdout.write("1. Démarrer le serveur: python manage.py runserver")
        self.stdout.write("2. Accéder à l'app: http://localhost:8000")
        self.stdout.write("3. Admin Django: http://localhost:8000/admin")
        
        self.stdout.write("\n🔑 Comptes de test:")
        self.stdout.write("• admin / Admin123! (Administrateur)")
        self.stdout.write("• abdoulaye / laye123! (Médecin)")
        self.stdout.write("• test / Test123! (Patient)")
