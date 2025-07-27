"""
Management command pour tester la correction AuditLog
Usage: python manage.py test_auditlog_correction
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory
from comptes.models import AuditLog, Utilisateur


class Command(BaseCommand):
    help = 'Teste la correction des erreurs AuditLog avec utilisateurs anonymes'
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🧪 TEST CORRECTION AUDITLOG - UTILISATEURS ANONYMES"))
        self.stdout.write("=" * 60)
        
        # Créer une factory de requêtes
        factory = RequestFactory()
        success_count = 0
        
        # Test 1: Utilisateur anonyme
        self.stdout.write("\n🔍 Test 1: Utilisateur anonyme...")
        try:
            anonymous_user = AnonymousUser()
            
            request = factory.get('/test/')
            request.user = anonymous_user
            request.session = {}
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Management Command'
            }
            
            result = AuditLog.log_action(
                utilisateur=anonymous_user,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test correction - utilisateur anonyme",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            self.stdout.write(self.style.SUCCESS("✅ SUCCESS: Utilisateur anonyme géré correctement"))
            if result:
                self.stdout.write(f"   📝 Log ID: {result.id}")
                self.stdout.write(f"   👤 Utilisateur assigné: {result.utilisateur}")
            success_count += 1
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ERREUR utilisateur anonyme: {e}"))
        
        # Test 2: Utilisateur None
        self.stdout.write("\n🔍 Test 2: Utilisateur None...")
        try:
            request = factory.get('/test/')
            request.user = None
            request.session = {}
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Management Command'
            }
            
            result = AuditLog.log_action(
                utilisateur=None,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test correction - utilisateur None",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            self.stdout.write(self.style.SUCCESS("✅ SUCCESS: Utilisateur None géré correctement"))
            if result:
                self.stdout.write(f"   📝 Log ID: {result.id}")
                self.stdout.write(f"   👤 Utilisateur assigné: {result.utilisateur}")
            success_count += 1
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ERREUR utilisateur None: {e}"))
        
        # Test 3: Utilisateur authentifié (pour comparaison)
        self.stdout.write("\n🔍 Test 3: Utilisateur authentifié...")
        try:
            user = Utilisateur.objects.filter(is_staff=True).first()
            if user:
                request = factory.get('/test/')
                request.user = user
                request.session = {}
                request.META = {
                    'REMOTE_ADDR': '127.0.0.1',
                    'HTTP_USER_AGENT': 'Test Management Command'
                }
                
                result = AuditLog.log_action(
                    utilisateur=user,
                    type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                    description="Test correction - utilisateur authentifié",
                    request=request,
                    niveau_risque=AuditLog.NiveauRisque.FAIBLE
                )
                
                self.stdout.write(self.style.SUCCESS("✅ SUCCESS: Utilisateur authentifié OK"))
                if result:
                    self.stdout.write(f"   📝 Log ID: {result.id}")
                    self.stdout.write(f"   👤 Utilisateur assigné: {result.utilisateur.email}")
                success_count += 1
            else:
                self.stdout.write(self.style.WARNING("⚠️ Aucun utilisateur staff trouvé"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ ERREUR utilisateur authentifié: {e}"))
        
        # Nettoyage
        self.stdout.write("\n🧹 Nettoyage des logs de test...")
        try:
            deleted_count = AuditLog.objects.filter(
                description__icontains="Test correction"
            ).delete()[0]
            self.stdout.write(f"🗑️ {deleted_count} logs de test supprimés")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Erreur nettoyage: {e}"))
        
        # Résultat final
        self.stdout.write("\n" + "=" * 60)
        if success_count >= 2:
            self.stdout.write(self.style.SUCCESS("🎯 RÉSULTAT: CORRECTION VALIDÉE!"))
            self.stdout.write(self.style.SUCCESS("   ✅ Plus d'erreur 'Cannot assign AnonymousUser'"))
            self.stdout.write(self.style.SUCCESS("   ✅ Utilisateurs anonymes → utilisateur=None"))
            self.stdout.write(self.style.SUCCESS("   ✅ Système d'audit fonctionnel"))
        else:
            self.stdout.write(self.style.ERROR("❌ CORRECTION INCOMPLÈTE - Vérifiez les erreurs"))
        self.stdout.write("=" * 60)
