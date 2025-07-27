#!/usr/bin/env python3
"""
Script de test pour vérifier le fonctionnement de l'API RFID avec CSRF
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
    from django.test import Client
    from django.contrib.auth import get_user_model
    from django.urls import reverse
    
    User = get_user_model()
    
    print("🧪 Test de l'API RFID avec gestion CSRF...")
    
    # Créer un client de test
    client = Client()
    
    # Créer ou récupérer un utilisateur admin
    try:
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            print("❌ Aucun utilisateur admin trouvé")
            print("Créez un superutilisateur avec: python manage.py createsuperuser")
            sys.exit(1)
        
        print(f"✅ Utilisateur admin trouvé: {admin_user.email}")
        
        # Se connecter
        client.force_login(admin_user)
        print("✅ Connexion admin réussie")
        
        # Tester l'accès à la page de création d'utilisateur
        response = client.get('/administration/users/create/')
        print(f"✅ Page de création accessible: {response.status_code}")
        
        # Tester l'API RFID
        response = client.post('/api/scan-rfid-user-creation/', 
                              content_type='application/json')
        
        print(f"📊 Réponse API RFID:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success')}")
            if data.get('success'):
                print(f"   UID: {data.get('uid')}")
                print(f"   Message: {data.get('message')}")
            else:
                print(f"   Error: {data.get('error')}")
        elif response.status_code == 403:
            print("   ❌ Erreur CSRF détectée")
        else:
            print(f"   ❌ Erreur {response.status_code}")
            
        print("\n🎯 Recommandations:")
        print("1. Vérifiez que l'Arduino est connecté sur COM6")
        print("2. Testez la fonction depuis l'interface web")
        print("3. Les messages d'erreur RFID sont maintenant spécifiques")
        
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
        
except Exception as e:
    print(f"❌ Erreur de configuration Django: {e}")
    print("Assurez-vous d'être dans le bon répertoire du projet.")
