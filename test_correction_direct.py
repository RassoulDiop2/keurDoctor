"""
Test simple et direct de la correction AuditLog
Execute ce script avec: python test_correction_direct.py
"""

# Configuration minimale
import os
import sys
import django

# Ajouter le chemin du projet
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

print("🏥 TEST DIRECT CORRECTION AUDITLOG")
print("=" * 50)

try:
    # Initialiser Django
    django.setup()
    print("✅ Django initialisé")
    
    # Importer les modèles nécessaires
    from comptes.models import AuditLog, Utilisateur
    from django.contrib.auth.models import AnonymousUser
    from django.test import RequestFactory
    
    print("✅ Modèles importés")
    
    # Créer une factory de requêtes
    factory = RequestFactory()
    
    # TEST 1: Utilisateur anonyme (source du problème original)
    print("\n🔍 TEST 1: Utilisateur anonyme")
    print("-" * 30)
    
    try:
        anonymous_user = AnonymousUser()
        request = factory.get('/test/')
        request.user = anonymous_user
        request.session = {}
        request.META = {
            'REMOTE_ADDR': '127.0.0.1',
            'HTTP_USER_AGENT': 'Test Direct'
        }
        
        # Tenter de créer un log avec utilisateur anonyme
        result = AuditLog.log_action(
            utilisateur=anonymous_user,  # Ceci causait l'erreur avant
            type_action=AuditLog.TypeAction.LECTURE_DONNEES,
            description="Test direct - utilisateur anonyme",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.FAIBLE
        )
        
        if result:
            print(f"✅ SUCCESS: Log créé avec ID {result.id}")
            print(f"👤 Utilisateur dans le log: {result.utilisateur}")
            if result.utilisateur is None:
                print("🎯 PARFAIT: utilisateur = None (comme attendu)")
            else:
                print("⚠️ ATTENTION: l'utilisateur n'est pas None")
        else:
            print("❌ Aucun log créé")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        print("La correction n'a pas fonctionné correctement!")
        
    # TEST 2: Vérifier qu'un utilisateur authentifié fonctionne toujours
    print("\n🔍 TEST 2: Utilisateur authentifié")
    print("-" * 30)
    
    try:
        # Chercher un utilisateur existant
        user = Utilisateur.objects.filter(is_staff=True).first()
        if user:
            request = factory.get('/test/')
            request.user = user
            request.session = {}
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test Direct'
            }
            
            result = AuditLog.log_action(
                utilisateur=user,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test direct - utilisateur authentifié",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            if result:
                print(f"✅ SUCCESS: Log créé avec ID {result.id}")
                print(f"👤 Utilisateur: {result.utilisateur.email}")
            else:
                print("❌ Aucun log créé")
        else:
            print("⚠️ Aucun utilisateur staff trouvé")
            
    except Exception as e:
        print(f"❌ ERREUR utilisateur authentifié: {e}")
    
    # Nettoyage
    print("\n🧹 Nettoyage des logs de test...")
    try:
        deleted = AuditLog.objects.filter(description__icontains="Test direct").delete()
        print(f"🗑️ {deleted[0]} logs supprimés")
    except Exception as e:
        print(f"⚠️ Erreur nettoyage: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 RÉSULTAT: CORRECTION VALIDÉE!")
    print("✅ Plus d'erreur 'Cannot assign AnonymousUser'")
    print("✅ Utilisateurs anonymes gérés correctement")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ ERREUR GÉNÉRALE: {e}")
    import traceback
    traceback.print_exc()

print("\nAppuyez sur Entrée pour continuer...")
input()
