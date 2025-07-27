#!/usr/bin/env python3
"""
Script de diagnostic pour tester la connexion RFID Arduino
"""
import os
import sys
import django
import serial
import time
import logging

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.rfid_arduino_handler import lire_uid_rfid

# Configuration logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_serial_connection():
    """Test direct de la connexion série"""
    print("=== TEST CONNEXION SÉRIE ===")
    
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        print(f"Ports série disponibles: {len(ports)}")
        for p in ports:
            print(f"- {p.device}: {p.description}")
        
        if not ports:
            print("❌ Aucun port série détecté!")
            return False
            
        # Test de COM6 spécifiquement
        port = 'COM6'
        print(f"\n=== TEST CONNEXION {port} ===")
        
        try:
            ser = serial.Serial(port, 9600, timeout=2)
            print(f"✅ Connexion établie sur {port}")
            time.sleep(1)
            
            # Test d'écriture/lecture
            print("📡 Test communication avec Arduino...")
            start_time = time.time()
            timeout = 5
            
            while time.time() - start_time < timeout:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        print(f"📨 Reçu: {line}")
                        ser.close()
                        return True
                time.sleep(0.1)
            
            print("⚠️ Aucune donnée reçue dans les 5 secondes")
            ser.close()
            return False
            
        except serial.SerialException as e:
            print(f"❌ Erreur connexion {port}: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test série: {e}")
        return False

def test_django_rfid_function():
    """Test de la fonction Django lire_uid_rfid()"""
    print("\n=== TEST FONCTION DJANGO ===")
    
    try:
        print("🔍 Test de lire_uid_rfid()...")
        uid = lire_uid_rfid()
        
        if uid:
            print(f"✅ UID détecté: {uid}")
            return True
        else:
            print("⚠️ Aucun UID détecté")
            return False
            
    except Exception as e:
        print(f"❌ Erreur fonction Django: {e}")
        return False

def test_arduino_output():
    """Test pour voir la sortie brute d'Arduino"""
    print("\n=== TEST SORTIE ARDUINO BRUTE ===")
    port = 'COM6'
    
    try:
        ser = serial.Serial(port, 9600, timeout=1)
        print(f"📡 Écoute sur {port} pendant 10 secondes...")
        print("Présentez une carte RFID maintenant!")
        
        start_time = time.time()
        timeout = 10
        received_data = False
        
        while time.time() - start_time < timeout:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"📨 [{time.strftime('%H:%M:%S')}] {line}")
                    received_data = True
            time.sleep(0.1)
        
        ser.close()
        
        if not received_data:
            print("❌ Aucune donnée reçue d'Arduino")
            print("Vérifiez:")
            print("1. Arduino est-il alimenté et connecté?")
            print("2. Le code RFID est-il chargé sur Arduino?")
            print("3. Le lecteur RFID est-il correctement câblé?")
            return False
        else:
            print("✅ Communication Arduino OK")
            return True
            
    except Exception as e:
        print(f"❌ Erreur test Arduino: {e}")
        return False

def main():
    """Fonction principale de diagnostic"""
    print("🔧 DIAGNOSTIC SYSTÈME RFID KEURDOCTOR")
    print("=" * 50)
    
    # Test 1: Connexion série
    serial_ok = test_serial_connection()
    
    # Test 2: Sortie Arduino brute
    arduino_ok = test_arduino_output()
    
    # Test 3: Fonction Django
    django_ok = test_django_rfid_function()
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DIAGNOSTIC")
    print("=" * 50)
    print(f"Connexion série: {'✅' if serial_ok else '❌'}")
    print(f"Communication Arduino: {'✅' if arduino_ok else '❌'}")
    print(f"Fonction Django: {'✅' if django_ok else '❌'}")
    
    if serial_ok and arduino_ok and django_ok:
        print("\n🎉 SYSTÈME RFID FONCTIONNEL!")
    else:
        print("\n🚨 PROBLÈMES DÉTECTÉS:")
        if not serial_ok:
            print("- Vérifiez la connexion USB Arduino")
        if not arduino_ok:
            print("- Vérifiez le code Arduino et le câblage RFID")
        if not django_ok:
            print("- Vérifiez la configuration Django RFID")

if __name__ == "__main__":
    main()
