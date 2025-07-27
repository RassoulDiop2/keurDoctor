import serial
import json
import time
import logging
from django.conf import settings
from .models import RFIDCard, Utilisateur, HistoriqueAuthentification
from django.utils import timezone

logger = logging.getLogger(__name__)

def lire_uid_rfid():
    """
    Fonction pour lire l'UID d'une carte RFID depuis Arduino.
    Gère les erreurs de connexion et retourne None en cas d'échec.
    """
    port = 'COM6'
    baudrate = 9600
    timeout = 5
    
    try:
        # Vérifier que le port est disponible
        import serial.tools.list_ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        if port not in available_ports:
            logger.warning(f"Port {port} non disponible. Ports disponibles: {available_ports}")
            return None
            
        ser = serial.Serial(port, baudrate, timeout=timeout)
        time.sleep(1)  # Attendre que la connexion s'établisse
        
        try:
            start = time.time()
            while time.time() - start < timeout:
                if ser.in_waiting > 0:
                    line = ser.readline().decode('utf-8').strip()
                    if line:
                        logger.info(f"Données reçues d'Arduino: {line}")
                        
                        # Essayer de parser en JSON d'abord
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
                            # Format texte simple
                            if len(line) >= 8:  # Un UID doit avoir au moins 8 caractères
                                logger.info(f"UID carte détecté: {line}")
                                return line
                
                time.sleep(0.1)  # Éviter une boucle trop intensive
                
            logger.info("Timeout - Aucune carte détectée")
            return None
            
        finally:
            ser.close()
            
    except serial.SerialException as e:
        logger.error(f"Erreur de connexion série sur {port}: {e}")
        return None
    except PermissionError as e:
        logger.error(f"Erreur de permission pour le port {port}: {e}")
        return None
    except Exception as e:
        logger.error(f"Erreur inattendue lors de la lecture RFID: {e}")
        return None


class ArduinoRFIDHandler:
    """Gestionnaire pour la communication avec Arduino RFID"""
    
    def __init__(self, port='COM3', baudrate=9600):
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
            line = self.serial_connection.readline().decode('utf-8').strip()
            
            if line.startswith('{') and line.endswith('}'):
                try:
                    data = json.loads(line)
                    return data.get('card_uid')
                except json.JSONDecodeError:
                    logger.warning(f"Données JSON invalides: {line}")
                    return None
            elif line.startswith('Carte détectée - UID: '):
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


if __name__ == "__main__":
    pass
