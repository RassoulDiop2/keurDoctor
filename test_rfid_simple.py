#!/usr/bin/env python3
"""
Script de diagnostic RFID simple
"""
import serial
import serial.tools.list_ports
import time

def main():
    print("=== DIAGNOSTIC RFID SIMPLE ===")
    
    # 1. Liste des ports
    ports = list(serial.tools.list_ports.comports())
    print(f"Ports série: {len(ports)}")
    for p in ports:
        print(f"- {p.device}: {p.description}")
    
    if not ports:
        print("Aucun port série!")
        return
    
    # 2. Test COM6
    port = 'COM6'
    try:
        print(f"\nTest {port}...")
        ser = serial.Serial(port, 9600, timeout=2)
        print("Connexion OK")
        
        # Attendre 3 secondes pour des données
        print("Écoute 3 secondes...")
        start = time.time()
        data_found = False
        
        while time.time() - start < 3:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"Reçu: {line}")
                    data_found = True
                    break
            time.sleep(0.1)
        
        if not data_found:
            print("Aucune donnée reçue")
        
        ser.close()
        
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    main()
    print("Diagnostic terminé.")
