import serial
import json
import time
import logging
from django.conf import settings
from .models import RFIDCard, Utilisateur, HistoriqueAuthentification
from django.utils import timezone

logger = logging.getLogger(__name__)

class ArduinoRFIDHandler:
    """Gestionnaire pour la communication avec Arduino RFID"""
    
    def __init__(self, port='COM3', baudrate=9600):
        """
        Initialise la connexion avec Arduino
        port: Port série (COM3 sur Windows, /dev/ttyUSB0 sur Linux)
        baudrate: Vitesse de communication
        """
        self.port = port
        self.baudrate = baudrate
        self.serial_connection = None
        self.is_connected = False
        
    def connect(self):
        """Établit la connexion avec Arduino"""
        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )
            self.is_connected = True
            logger.info(f"Connexion Arduino établie sur {self.port}")
            return True
        except serial.SerialException as e:
            logger.error(f"Erreur de connexion Arduino: {e}")
            return False
    
    def disconnect(self):
        """Ferme la connexion avec Arduino"""
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
            self.is_connected = False
            logger.info("Connexion Arduino fermée")
    
    def read_card_uid(self):
        """Lit l'UID d'une carte RFID depuis Arduino"""
        if not self.is_connected:
            if not self.connect():
                return None
        
        try:
            # Lire une ligne depuis Arduino
            line = self.serial_connection.readline().decode('utf-8').strip()
            
            if line.startswith('{') and line.endswith('}'):
                # Tenter de parser le JSON
                try:
                    data = json.loads(line)
                    return data.get('card_uid')
                except json.JSONDecodeError:
                    logger.warning(f"Données JSON invalides: {line}")
                    return None
            elif line.startswith('Carte détectée - UID: '):
                # Format alternatif
                uid = line.replace('Carte détectée - UID: ', '')
                return uid
            else:
                return None
                
        except serial.SerialException as e:
            logger.error(f"Erreur de lecture Arduino: {e}")
            self.is_connected = False
            return None
    
    def authenticate_user_by_rfid(self, card_uid):
        """Authentifie un utilisateur par sa carte RFID"""
        try:
            # Chercher la carte RFID dans la base de données
            rfid_card = RFIDCard.objects.get(
                card_uid=card_uid,
                actif=True
            )
            
            user = rfid_card.utilisateur
            
            # Vérifier si l'utilisateur est actif et non bloqué
            if not user.est_actif or user.est_bloque:
                logger.warning(f"Utilisateur {user.email} bloqué ou inactif")
                return None, "Utilisateur bloqué ou inactif"
            
            # Enregistrer l'authentification réussie
            HistoriqueAuthentification.objects.create(
                utilisateur=user,
                type_auth=HistoriqueAuthentification.TypeAuth.NFC_CARTE,
                succes=True,
                adresse_ip='Arduino_RFID',
                user_agent='Arduino_RFID_Reader',
                role_tente=user.role_autorise,
                role_autorise=user.role_autorise
            )
            
            # Mettre à jour la dernière connexion
            user.date_derniere_connexion = timezone.now()
            user.save()
            
            logger.info(f"Authentification RFID réussie pour {user.email}")
            return user, "Authentification réussie"
            
        except RFIDCard.DoesNotExist:
            logger.warning(f"Carte RFID non reconnue: {card_uid}")
            return None, "Carte RFID non reconnue"
        except Exception as e:
            logger.error(f"Erreur d'authentification RFID: {e}")
            return None, f"Erreur: {str(e)}"
    
    def run_continuous_reading(self, callback=None):
        """Lecture continue des cartes RFID"""
        logger.info("Démarrage de la lecture continue RFID")
        
        while self.is_connected:
            card_uid = self.read_card_uid()
            
            if card_uid:
                user, message = self.authenticate_user_by_rfid(card_uid)
                
                if callback:
                    callback(user, message, card_uid)
                else:
                    if user:
                        print(f"✅ Authentification réussie: {user.email}")
                    else:
                        print(f"❌ Échec: {message}")
            
            time.sleep(0.1)  # Petite pause pour éviter de surcharger


def test_arduino_connection():
    """Fonction de test pour vérifier la connexion Arduino"""
    handler = ArduinoRFIDHandler()
    
    if handler.connect():
        print("✅ Connexion Arduino établie")
        print("Présentez une carte RFID...")
        
        # Test pendant 30 secondes
        start_time = time.time()
        while time.time() - start_time < 30:
            card_uid = handler.read_card_uid()
            if card_uid:
                print(f"📋 Carte détectée: {card_uid}")
                user, message = handler.authenticate_user_by_rfid(card_uid)
                if user:
                    print(f"✅ Utilisateur authentifié: {user.email}")
                else:
                    print(f"❌ {message}")
                break
            time.sleep(0.1)
        
        handler.disconnect()
    else:
        print("❌ Impossible de se connecter à Arduino")
        print("Vérifiez le port série et les connexions")


if __name__ == "__main__":
    test_arduino_connection() 