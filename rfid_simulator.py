#!/usr/bin/env python3
"""
Simulateur RFID pour tests KeurDoctor
Permet de simuler une carte RFID quand l'Arduino ne fonctionne pas
"""
import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from comptes.models import RFIDCard, Utilisateur

def simuler_carte_rfid():
    """Simule une carte RFID pour les tests"""
    print("=== SIMULATEUR RFID KEURDOCTOR ===")
    
    # Lister les cartes RFID disponibles
    cartes = RFIDCard.objects.filter(actif=True).select_related('utilisateur')
    
    if not cartes.exists():
        print("❌ Aucune carte RFID active trouvée dans la base de données")
        print("Veuillez créer une carte RFID via l'admin Django")
        return None
    
    print("🔍 Cartes RFID disponibles:")
    for i, carte in enumerate(cartes, 1):
        user = carte.utilisateur
        print(f"{i}. UID: {carte.card_uid}")
        print(f"   Utilisateur: {user.prenom} {user.nom} ({user.email})")
        print(f"   Rôle: {user.role_autorise}")
        print(f"   Actif: {'✅' if user.est_actif else '❌'}")
        print("")
    
    # Demander à l'utilisateur de choisir
    try:
        choix = input("Choisissez une carte (numéro) ou ENTER pour la première: ").strip()
        
        if not choix:
            carte_choisie = cartes.first()
        else:
            index = int(choix) - 1
            carte_choisie = list(cartes)[index]
        
        print(f"\n✅ Simulation carte UID: {carte_choisie.card_uid}")
        print(f"Utilisateur: {carte_choisie.utilisateur.prenom} {carte_choisie.utilisateur.nom}")
        
        return carte_choisie.card_uid
        
    except (ValueError, IndexError):
        print("❌ Choix invalide")
        return None

def patcher_fonction_rfid():
    """Patch temporaire de la fonction lire_uid_rfid()"""
    print("\n🔧 PATCH TEMPORAIRE DE LA FONCTION RFID")
    print("Cette solution contourne le problème Arduino")
    
    # Créer le fichier patch
    patch_content = '''"""
PATCH TEMPORAIRE RFID - Simulateur de carte
À utiliser quand l'Arduino ne fonctionne pas
"""
import logging

logger = logging.getLogger(__name__)

# UID de carte simulée (sera remplacé par le choix utilisateur)
SIMULATED_UID = "DEFAULT_UID"

def lire_uid_rfid():
    """
    Version simulée de lire_uid_rfid() qui retourne toujours le même UID
    À utiliser temporairement quand l'Arduino ne fonctionne pas
    """
    logger.info(f"🎭 SIMULATION RFID - UID retourné: {SIMULATED_UID}")
    return SIMULATED_UID

# Sauvegarde de la fonction originale (si nécessaire)
def lire_uid_rfid_original():
    """Fonction originale (désactivée)"""
    import serial
    import json
    import time
    
    port = 'COM6'
    baudrate = 9600
    timeout = 5
    
    try:
        import serial.tools.list_ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        if port not in available_ports:
            logger.warning(f"Port {port} non disponible. Ports disponibles: {available_ports}")
            return None
            
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(1)
        
        try:
            start = time.time()
            while time.time() - start < timeout:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        logger.info(f"Données reçues d'Arduino: {line}")
                        
                        if line.startswith('{'):
                            try:
                                data = json.loads(line)
                                uid = data.get('uid') or data.get('card_uid')
                                if uid:
                                    logger.info(f"UID carte détecté: {uid}")
                                    return uid
                            except json.JSONDecodeError:
                                logger.warning(f"Données JSON invalides: {line}")
                        else:
                            if len(line) >= 8:
                                logger.info(f"UID carte détecté: {line}")
                                return line
                
                time.sleep(0.1)
                
            logger.info("Timeout - Aucune carte détectée")
            return None
            
        finally:
            ser.close()
            
    except Exception as e:
        logger.error(f"Erreur lecture RFID: {e}")
        return None
'''
    
    return patch_content

def main():
    print("🚨 ATTENTION: L'Arduino RFID ne répond pas!")
    print("Cette situation peut être due à:")
    print("1. Arduino non programmé avec le code RFID")
    print("2. Lecteur RFID mal connecté ou défectueux") 
    print("3. Arduino déconnecté ou en panne")
    print("4. Driver USB Arduino manquant")
    print("")
    
    response = input("Voulez-vous créer un patch temporaire pour contourner le problème ? (o/n): ").lower().strip()
    
    if response == 'o':
        # Choisir une carte à simuler
        uid_choisi = simuler_carte_rfid()
        
        if uid_choisi:
            # Créer le patch
            patch_code = patcher_fonction_rfid()
            patch_code = patch_code.replace('SIMULATED_UID = "DEFAULT_UID"', f'SIMULATED_UID = "{uid_choisi}"')
            
            # Sauvegarder le patch
            patch_file = 'rfid_patch_temporaire.py'
            with open(patch_file, 'w', encoding='utf-8') as f:
                f.write(patch_code)
            
            print(f"\n✅ Patch créé: {patch_file}")
            print("📋 INSTRUCTIONS:")
            print("1. Copiez le contenu du patch dans comptes/rfid_arduino_handler.py")
            print("2. Remplacez la fonction lire_uid_rfid() existante")
            print("3. Testez l'accès RFID sur l'interface web")
            print("4. Restaurez le code original une fois l'Arduino réparé")
            print("")
            print("⚠️  IMPORTANT: Ce patch est temporaire et doit être retiré")
            print("   une fois le problème Arduino résolu!")
        else:
            print("❌ Impossible de créer le patch sans carte valide")
    else:
        print("❌ Patch annulé. Veuillez réparer l'Arduino pour utiliser RFID.")

if __name__ == "__main__":
    main()
