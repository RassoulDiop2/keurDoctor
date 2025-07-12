from django.core.management.base import BaseCommand
from django.test import Client
from django.contrib.auth import get_user_model
from comptes.models import AuditLog, AlerteSecurite
from django.urls import reverse

User = get_user_model()

class Command(BaseCommand):
    help = 'Teste automatiquement les mécanismes de sécurité'

    def handle(self, *args, **options):
        self.stdout.write("🧪 Démarrage des tests de sécurité automatiques...")
        
        # Créer un client de test
        client = Client()
        
        # Test 1: Tentative d'accès sans authentification
        self.stdout.write("\n1️⃣ Test: Accès sans authentification")
        response = client.get('/test/acces/medecin/')
        if response.status_code == 302:  # Redirection vers login
            self.stdout.write(self.style.SUCCESS("✅ Accès refusé correctement (redirection login)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec: Status {response.status_code}"))
        
        # Test 2: Tentative d'usurpation de rôle
        self.stdout.write("\n2️⃣ Test: Usurpation de rôle")
        
        # Créer un utilisateur patient de test
        patient, created = User.objects.get_or_create(
            email='test.patient@keurdoctor.com',
            defaults={
                'prenom': 'Test',
                'nom': 'Patient',
                'role_autorise': 'patient',
                'est_actif': True
            }
        )
        
        # Se connecter en tant que patient
        client.force_login(patient)
        
        # Tenter d'accéder aux données médecin
        response = client.get('/test/acces/medecin/')
        if response.status_code == 403:  # Accès interdit
            self.stdout.write(self.style.SUCCESS("✅ Accès refusé correctement (403 Forbidden)"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec: Status {response.status_code}"))
        
        # Test 3: Tentative d'élévation de privilèges
        self.stdout.write("\n3️⃣ Test: Élévation de privilèges")
        response = client.get('/test/acces/admin/')
        if response.status_code == 403:
            self.stdout.write(self.style.SUCCESS("✅ Élévation de privilèges bloquée"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec: Status {response.status_code}"))
        
        # Test 4: Vérifier les logs d'audit
        self.stdout.write("\n4️⃣ Test: Vérification des logs d'audit")
        logs_audit = AuditLog.objects.filter(
            utilisateur=patient,
            type_action=AuditLog.TypeAction.VIOLATION_SECURITE
        ).count()
        
        if logs_audit > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ {logs_audit} violations de sécurité loggées"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Aucune violation loggée"))
        
        # Test 5: Vérifier les alertes de sécurité
        self.stdout.write("\n5️⃣ Test: Vérification des alertes")
        alertes = AlerteSecurite.objects.filter(
            utilisateur_concerne=patient
        ).count()
        
        if alertes > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ {alertes} alertes de sécurité créées"))
        else:
            self.stdout.write(self.style.WARNING("⚠️ Aucune alerte créée"))
        
        # Test 6: Test avec un médecin
        self.stdout.write("\n6️⃣ Test: Accès légitime médecin")
        medecin, created = User.objects.get_or_create(
            email='test.medecin@keurdoctor.com',
            defaults={
                'prenom': 'Test',
                'nom': 'Médecin',
                'role_autorise': 'medecin',
                'est_actif': True
            }
        )
        
        client.force_login(medecin)
        response = client.get('/test/acces/medecin/')
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("✅ Accès médecin autorisé correctement"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec accès médecin: Status {response.status_code}"))
        
        # Test 7: Test avec un admin
        self.stdout.write("\n7️⃣ Test: Accès légitime admin")
        admin, created = User.objects.get_or_create(
            email='test.admin@keurdoctor.com',
            defaults={
                'prenom': 'Test',
                'nom': 'Admin',
                'role_autorise': 'admin',
                'est_actif': True
            }
        )
        
        client.force_login(admin)
        response = client.get('/test/acces/admin/')
        if response.status_code == 200:
            self.stdout.write(self.style.SUCCESS("✅ Accès admin autorisé correctement"))
        else:
            self.stdout.write(self.style.ERROR(f"❌ Échec accès admin: Status {response.status_code}"))
        
        # Résumé final
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("🎉 Tests de sécurité terminés!"))
        self.stdout.write("📊 Résumé:")
        self.stdout.write(f"   - Violations détectées: {logs_audit}")
        self.stdout.write(f"   - Alertes créées: {alertes}")
        self.stdout.write(f"   - Tests d'accès: 7/7 effectués")
        
        # Nettoyage
        for user in [patient, medecin, admin]:
            if user.email.startswith('test.'):
                user.delete()
        
        self.stdout.write("🧹 Utilisateurs de test supprimés") 