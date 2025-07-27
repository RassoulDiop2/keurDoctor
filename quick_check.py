#!/usr/bin/env python3
"""
Script pour vérifier l'état du système rapidement
"""
print("🔍 VÉRIFICATION RAPIDE DU SYSTÈME")
print("=" * 50)

# Test 1: Importation Django
try:
    import os
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
    django.setup()
    print("✅ Configuration Django OK")
except Exception as e:
    print(f"❌ Erreur configuration Django: {e}")
    exit(1)

# Test 2: Modèles
try:
    from comptes.models import Utilisateur, AuditLog
    print("✅ Importation des modèles OK")
except Exception as e:
    print(f"❌ Erreur importation modèles: {e}")

# Test 3: Connexion DB
try:
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
    print("✅ Connexion base de données OK")
except Exception as e:
    print(f"❌ Erreur base de données: {e}")

# Test 4: Compter les utilisateurs
try:
    user_count = Utilisateur.objects.count()
    print(f"✅ Utilisateurs en base: {user_count}")
except Exception as e:
    print(f"❌ Erreur comptage utilisateurs: {e}")

# Test 5: Derniers utilisateurs
try:
    recent_users = Utilisateur.objects.order_by('-date_creation')[:3]
    print(f"📋 Derniers utilisateurs:")
    for user in recent_users:
        print(f"   - {user.email} ({user.role_autorise})")
except Exception as e:
    print(f"❌ Erreur récupération utilisateurs: {e}")

# Test 6: AuditLog
try:
    audit_count = AuditLog.objects.count()
    print(f"✅ Entrées AuditLog: {audit_count}")
except Exception as e:
    print(f"❌ Erreur AuditLog: {e}")

# Test 7: Services externes
try:
    import requests
    
    # Django
    try:
        response = requests.get("http://127.0.0.1:8000/", timeout=2)
        print(f"✅ Django serveur accessible (status: {response.status_code})")
    except:
        print("❌ Django serveur non accessible")
    
    # Keycloak
    try:
        response = requests.get("http://localhost:8080/", timeout=2)
        print(f"✅ Keycloak accessible (status: {response.status_code})")
    except:
        print("❌ Keycloak non accessible")
        
except ImportError:
    print("⚠️  Requests non disponible pour test services externes")

print("\n✅ Vérification terminée")
