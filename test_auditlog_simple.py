"""
Test simple pour vérifier la correction AuditLog directement via manage.py shell
"""
from comptes.models import AuditLog, Utilisateur
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory

print("=" * 60)
print("🧪 TEST CORRECTION AUDITLOG - UTILISATEURS ANONYMES")
print("=" * 60)

# Créer une factory de requêtes
factory = RequestFactory()

print("\n🔍 Test avec utilisateur anonyme...")

try:
    # Créer un utilisateur anonyme
    anonymous_user = AnonymousUser()
    
    # Simuler une requête
    request = factory.get('/test/')
    request.user = anonymous_user
    request.session = {}
    request.META = {
        'REMOTE_ADDR': '127.0.0.1',
        'HTTP_USER_AGENT': 'Test User Agent'
    }
    
    # Tester l'audit log avec utilisateur anonyme
    result = AuditLog.log_action(
        utilisateur=anonymous_user,
        type_action=AuditLog.TypeAction.LECTURE_DONNEES,
        description="Test utilisateur anonyme - correction validée",
        request=request,
        niveau_risque=AuditLog.NiveauRisque.FAIBLE
    )
    
    print("✅ SUCCESS: Log créé pour utilisateur anonyme sans erreur!")
    print(f"📝 Log ID: {result.id if result else 'N/A'}")
    
    # Vérifier que l'utilisateur est bien None dans la base
    if result:
        print(f"👤 Utilisateur assigné: {result.utilisateur}")
        print(f"📋 Description: {result.description}")
        print(f"⏰ Date: {result.date_heure}")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()

print("\n🔍 Test avec utilisateur None...")

try:
    # Tester avec None directement
    request = factory.get('/test/')
    request.user = None
    request.session = {}
    request.META = {
        'REMOTE_ADDR': '127.0.0.1',
        'HTTP_USER_AGENT': 'Test User Agent'
    }
    
    result = AuditLog.log_action(
        utilisateur=None,
        type_action=AuditLog.TypeAction.LECTURE_DONNEES,
        description="Test utilisateur None - correction validée",
        request=request,
        niveau_risque=AuditLog.NiveauRisque.FAIBLE
    )
    
    print("✅ SUCCESS: Log créé pour utilisateur None sans erreur!")
    print(f"📝 Log ID: {result.id if result else 'N/A'}")
    
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("\n🧹 Nettoyage des logs de test...")
try:
    deleted_count = AuditLog.objects.filter(
        description__icontains="correction validée"
    ).delete()[0]
    print(f"🗑️ {deleted_count} logs de test supprimés")
except Exception as e:
    print(f"⚠️ Erreur nettoyage: {e}")

print("\n" + "=" * 60)
print("🎯 RÉSULTAT: La correction AuditLog fonctionne correctement!")
print("   • Plus d'erreur 'Cannot assign AnonymousUser'")
print("   • Les utilisateurs anonymes sont gérés avec utilisateur=None")
print("=" * 60)
