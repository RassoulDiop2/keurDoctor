from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from comptes.models import Utilisateur

User = get_user_model()


class Command(BaseCommand):
    help = 'Configure les rôles autorisés pour les utilisateurs existants'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force la mise à jour même si le rôle est déjà défini',
        )

    def handle(self, *args, **options):
        self.stdout.write("🔐 Configuration des rôles autorisés...")
        
        # Mapping des utilisateurs existants vers leurs rôles (par email)
        user_roles = {
            'admin@keurdoctor.com': 'admin',
            'dr.laye@keurdoctor.com': 'medecin',
            'patient@test.com': 'patient',
        }
        
        updated_count = 0
        
        for email, role in user_roles.items():
            try:
                # Chercher l'utilisateur par email
                user = User.objects.get(email=email)
                
                # Vérifier si le rôle autorisé est défini
                if user.role_autorise is None or options['force']:
                    user.role_autorise = role
                    user.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Rôle '{role}' défini pour {email}")
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  Rôle déjà défini pour {email}: {user.role_autorise}")
                    )
                    
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  Utilisateur {email} non trouvé")
                )
        
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"🎉 Configuration terminée!"))
        self.stdout.write(f"Rôles mis à jour: {updated_count}")
        
        self.stdout.write("\n📋 Rôles configurés:")
        self.stdout.write("| Email | Rôle Autorisé |")
        self.stdout.write("|-------|---------------|")
        for email, role in user_roles.items():
            self.stdout.write(f"| {email} | {role} |")
        
        self.stdout.write(f"\n🔧 Prochaines étapes:")
        self.stdout.write("1. Testez la connexion avec les différents rôles")
        self.stdout.write("2. Vérifiez que le blocage fonctionne correctement")
        self.stdout.write("3. Accédez à /admin/securite/ pour gérer les alertes") 