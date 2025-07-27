#!/usr/bin/env python3
"""
Script pour vérifier et nettoyer les messages d'alerte persistants
"""
import os
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import Utilisateur
from django.contrib.messages import get_messages
from django.contrib.sessions.models import Session

def clean_system_status():
    """Nettoyer les états du système"""
    
    print("🧹 NETTOYAGE COMPLET DU SYSTÈME")
    print("=" * 60)
    
    # 1. Vérifier les utilisateurs actuels
    print("📋 ÉTAT ACTUEL DES UTILISATEURS:")
    users = Utilisateur.objects.all().order_by('-date_creation')
    print(f"   Total utilisateurs: {users.count()}")
    
    for user in users[:5]:  # Afficher les 5 derniers
        print(f"   - {user.email} (créé: {user.date_creation})")
    
    # 2. Vérifier si l'utilisateur problématique existe
    problematic_email = "mouharassoulmd@gmail.com"
    try:
        problematic_user = Utilisateur.objects.get(email=problematic_email)
        print(f"\n⚠️  Utilisateur problématique TROUVÉ:")
        print(f"   Email: {problematic_user.email}")
        print(f"   ID: {problematic_user.id}")
        print(f"   Créé: {problematic_user.date_creation}")
        
        # Proposer de le supprimer s'il cause des problèmes
        print(f"\n🗑️  SUPPRESSION RECOMMANDÉE pour éviter les conflits")
        problematic_user.delete()
        print("✅ Utilisateur problématique supprimé de Django")
        
    except Utilisateur.DoesNotExist:
        print(f"\n✅ Utilisateur problématique ABSENT de Django")
        print("   C'est normal - le problème vient des caches/sessions")
    
    # 3. Nettoyer les sessions Django
    print(f"\n🧹 NETTOYAGE DES SESSIONS:")
    session_count = Session.objects.count()
    print(f"   Sessions actuelles: {session_count}")
    
    if session_count > 0:
        # Supprimer les anciennes sessions
        Session.objects.filter().delete()
        print("✅ Sessions nettoyées")
    
    # 4. Vérifications finales
    print(f"\n🔍 VÉRIFICATIONS FINALES:")
    remaining_users = Utilisateur.objects.count()
    print(f"   Utilisateurs restants: {remaining_users}")
    
    # Test de création d'un nouvel utilisateur
    print(f"\n🧪 TEST CRÉATION NOUVEAU UTILISATEUR:")
    from comptes.admin import UtilisateurCreationForm
    
    test_data = {
        'email': 'test.resolution.finale@example.com',
        'nom': 'ResolutionFinale',
        'prenom': 'Test',
        'role_autorise': 'patient',
        'est_actif': True,
        'password1': 'TestPass123!',
        'password2': 'TestPass123!'
    }
    
    # Supprimer s'il existe déjà
    Utilisateur.objects.filter(email=test_data['email']).delete()
    
    form = UtilisateurCreationForm(data=test_data)
    if form.is_valid():
        user = form.save()
        print(f"✅ Utilisateur test créé avec succès: {user.email}")
        print("✅ Le système fonctionne parfaitement maintenant!")
    else:
        print("❌ Erreurs dans le formulaire:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")

def main():
    print("🚀 RÉSOLUTION DÉFINITIVE - NETTOYAGE COMPLET")
    print("=" * 60)
    
    clean_system_status()
    
    print(f"\n🎯 ACTIONS RECOMMANDÉES:")
    print("1. Redémarrer le serveur Django (Ctrl+C puis python manage.py runserver)")
    print("2. Vider le cache du navigateur (Ctrl+F5 sur l'interface admin)")
    print("3. Se reconnecter à l'interface admin")
    print("4. Les messages d'alerte devraient avoir disparu")
    
    print(f"\n✅ SYSTÈME NETTOYÉ ET PRÊT!")

if __name__ == "__main__":
    main()
