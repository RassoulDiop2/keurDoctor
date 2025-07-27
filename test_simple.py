import os
os.chdir(r'h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app')

import django
from django.conf import settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

print("=== Test RFID avec CSRF ===")

# Test 1: Configuration
print("1. Configuration Django OK")

# Test 2: Client de test
client = Client()
print("2. Client de test créé")

# Test 3: Utilisateur admin
User = get_user_model()
admin_user = User.objects.filter(is_staff=True).first()
if admin_user:
    print(f"3. Admin trouvé: {admin_user.email}")
    client.force_login(admin_user)
    
    # Test 4: API RFID
    try:
        response = client.post('/api/scan-rfid-user-creation/')
        print(f"4. Réponse API: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Success: {data.get('success', False)}")
            print(f"   Message: {data.get('message', data.get('error', 'N/A'))}")
        elif response.status_code == 403:
            print("   ❌ Erreur CSRF")
        else:
            print(f"   ❌ Erreur {response.status_code}")
            
    except Exception as e:
        print(f"4. Erreur API: {e}")
else:
    print("3. ❌ Aucun admin trouvé")

print("=== Fin du test ===")
