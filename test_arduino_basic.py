#!/usr/bin/env python3
"""
Test de base Arduino - Vérification connexion
"""
import serial
import time

def test_arduino_basic():
    try:
        print("Test connexion Arduino COM6...")
        ser = serial.Serial('COM6', 9600, timeout=1)
        time.sleep(2)  # Attendre reset Arduino
        
        # Envoyer commande test
        ser.write(b'TEST\n')
        time.sleep(0.5)
        
        # Lire réponse (avec timeout court)
        if ser.in_waiting > 0:
            response = ser.readline().decode('utf-8', errors='ignore').strip()
            print(f"Réponse Arduino: {response}")
        else:
            print("Aucune réponse d'Arduino")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"Erreur: {e}")
        return False

if __name__ == "__main__":
    test_arduino_basic()
    print("Test terminé.")
