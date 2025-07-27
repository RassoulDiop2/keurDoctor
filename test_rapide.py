"""
Test ultra-simple pour validation correction AuditLog
"""
import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')

django.setup()

from comptes.models import AuditLog
from django.contrib.auth.models import AnonymousUser

print("🧪 Test ultra-rapide correction AuditLog")

# Créer un utilisateur anonyme
anonymous_user = AnonymousUser()

try:
    # Tester la méthode log_action avec utilisateur anonyme
    result = AuditLog.log_action(
        utilisateur=anonymous_user,
        type_action=AuditLog.TypeAction.LECTURE_DONNEES,
        description="Test rapide anonyme",
        niveau_risque=AuditLog.NiveauRisque.FAIBLE
    )
    
    if result:
        print(f"✅ SUCCESS! Log créé: ID={result.id}, utilisateur={result.utilisateur}")
        # Nettoyer
        result.delete()
        print("🧹 Log nettoyé")
    else:
        print("❌ Aucun résultat")
        
except Exception as e:
    print(f"❌ ERREUR: {e}")

print("🎯 Test terminé")
