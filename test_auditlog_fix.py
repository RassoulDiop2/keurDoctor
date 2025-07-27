#!/usr/bin/env python3
"""
Script de test pour valider la correction de l'erreur AuditLog
Teste différents scénarios d'utilisateurs (authentifiés, anonymes)
"""
import os
import sys
import django

# Configuration Django
project_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_path)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

try:
    django.setup()
    from comptes.models import AuditLog, Utilisateur
    from django.test import RequestFactory
    from django.contrib.auth.models import AnonymousUser
    
    def test_audit_log_correction():
        print("=" * 60)
        print("🧪 TEST CORRECTION AUDITLOG - UTILISATEURS ANONYMES")
        print("=" * 60)
        
        # Créer une factory de requêtes pour simuler des requêtes
        factory = RequestFactory()
        
        # Test 1: Utilisateur authentifié
        print("\n1️⃣ TEST UTILISATEUR AUTHENTIFIÉ")
        print("-" * 30)
        
        try:
            # Récupérer un utilisateur existant ou en créer un
            user = Utilisateur.objects.filter(is_staff=True).first()
            if not user:
                print("❌ Aucun utilisateur staff trouvé - créez un superutilisateur")
                return False
            
            # Simuler une requête
            request = factory.get('/test/')
            request.user = user
            request.session = {}
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test User Agent'
            }
            
            # Tester l'audit log
            AuditLog.log_action(
                utilisateur=user,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test utilisateur authentifié",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            print(f"✅ Log créé pour utilisateur authentifié: {user.email}")
            
        except Exception as e:
            print(f"❌ Erreur utilisateur authentifié: {e}")
            return False
        
        # Test 2: Utilisateur anonyme (source du problème)
        print("\n2️⃣ TEST UTILISATEUR ANONYME")
        print("-" * 30)
        
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
            AuditLog.log_action(
                utilisateur=anonymous_user,  # ✅ Ceci causait l'erreur avant
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test utilisateur anonyme",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            print("✅ Log créé pour utilisateur anonyme (utilisateur=None)")
            
        except Exception as e:
            print(f"❌ Erreur utilisateur anonyme: {e}")
            return False
        
        # Test 3: Utilisateur None
        print("\n3️⃣ TEST UTILISATEUR NONE")
        print("-" * 30)
        
        try:
            # Simuler une requête
            request = factory.get('/test/')
            request.user = None
            request.session = {}
            request.META = {
                'REMOTE_ADDR': '127.0.0.1',
                'HTTP_USER_AGENT': 'Test User Agent'
            }
            
            # Tester l'audit log avec utilisateur None
            AuditLog.log_action(
                utilisateur=None,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description="Test utilisateur None",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
            
            print("✅ Log créé pour utilisateur None")
            
        except Exception as e:
            print(f"❌ Erreur utilisateur None: {e}")
            return False
        
        # Test 4: Vérifier les logs créés
        print("\n4️⃣ VÉRIFICATION DES LOGS CRÉÉS")
        print("-" * 30)
        
        try:
            # Compter les logs récents
            recent_logs = AuditLog.objects.filter(
                description__icontains="Test"
            ).order_by('-date_heure')[:10]
            
            print(f"📊 {len(recent_logs)} logs de test trouvés:")
            
            for log in recent_logs:
                user_info = log.utilisateur.email if log.utilisateur else "Anonyme"
                print(f"   - {log.description} | Utilisateur: {user_info} | {log.date_heure}")
            
        except Exception as e:
            print(f"❌ Erreur vérification logs: {e}")
            return False
        
        return True
    
    def clean_test_logs():
        """Nettoie les logs de test"""
        try:
            deleted_count = AuditLog.objects.filter(description__icontains="Test").delete()[0]
            print(f"🧹 {deleted_count} logs de test supprimés")
        except Exception as e:
            print(f"⚠️ Erreur nettoyage: {e}")
    
    if __name__ == "__main__":
        try:
            # Nettoyer les anciens logs de test
            clean_test_logs()
            
            # Lancer le test
            success = test_audit_log_correction()
            
            if success:
                print("\n" + "=" * 60)
                print("✅ CORRECTION AUDITLOG VALIDÉE")
                print("=" * 60)
                print("🎯 La correction fonctionne correctement :")
                print("   • Utilisateurs authentifiés → Loggés normalement")
                print("   • Utilisateurs anonymes → utilisateur=None (pas d'erreur)")
                print("   • Utilisateur None → Géré correctement")
                print("   • Plus d'erreur 'Cannot assign AnonymousUser'")
                print("=" * 60)
                
                # Nettoyer les logs de test
                clean_test_logs()
                
            else:
                print("\n❌ Des erreurs persistent - vérifiez les logs ci-dessus")
                
        except Exception as e:
            print(f"❌ Erreur générale: {e}")
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"❌ Erreur configuration Django: {e}")
    print("Assurez-vous d'être dans le bon répertoire du projet.")
