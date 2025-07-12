from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Débloque l\'utilisateur admin'

    def handle(self, *args, **options):
        try:
            # Trouver l'utilisateur admin
            admin_user = User.objects.get(email='admin@keurdoctor.com')
            
            if admin_user.est_bloque:
                # Débloquer l'utilisateur
                admin_user.est_bloque = False
                admin_user.date_blocage = None
                admin_user.raison_blocage = ""
                admin_user.bloque_par_admin = None
                admin_user.tentatives_connexion_incorrectes = 0
                admin_user.derniere_tentative_incorrecte = None
                admin_user.save()
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Utilisateur admin {admin_user.email} débloqué avec succès!'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'ℹ️ L\'utilisateur admin {admin_user.email} n\'est pas bloqué.'
                    )
                )
                
        except User.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(
                    '❌ Utilisateur admin@keurdoctor.com non trouvé.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Erreur lors du déblocage: {e}'
                )
            ) 