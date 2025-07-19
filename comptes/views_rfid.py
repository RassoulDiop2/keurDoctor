from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import json
import logging
from django.contrib.admin.views.decorators import staff_member_required
import serial
import time

from .models import RFIDCard, Utilisateur, HistoriqueAuthentification
from .rfid_arduino_handler import ArduinoRFIDHandler

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["POST"])
def rfid_authenticate(request):
    """Vue pour l'authentification RFID via Arduino"""
    try:
        data = json.loads(request.body)
        card_uid = data.get('card_uid')
        
        if not card_uid:
            return JsonResponse({
                'success': False,
                'message': 'UID de carte manquant'
            }, status=400)
        
        # Utiliser le gestionnaire Arduino pour l'authentification
        handler = ArduinoRFIDHandler()
        user, message = handler.authenticate_user_by_rfid(card_uid)
        
        if user:
            # Connecter l'utilisateur
            login(request, user)
            
            return JsonResponse({
                'success': True,
                'message': f'Authentification réussie pour {user.email}',
                'user': {
                    'email': user.email,
                    'prenom': user.prenom,
                    'nom': user.nom,
                    'role': user.role_autorise
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'message': message
            }, status=401)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur d'authentification RFID: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur serveur'
        }, status=500)


def rfid_login_page(request):
    """Page de connexion RFID"""
    return render(request, 'rfid/rfid_login.html')


def register_rfid_card(request):
    """Page pour enregistrer une nouvelle carte RFID"""
    if request.method == 'POST':
        card_uid = request.POST.get('card_uid')
        user_id = request.POST.get('user_id')
        
        if card_uid and user_id:
            try:
                user = Utilisateur.objects.get(id=user_id)
                
                # Vérifier si la carte existe déjà
                if RFIDCard.objects.filter(card_uid=card_uid).exists():
                    messages.error(request, 'Cette carte RFID est déjà enregistrée')
                else:
                    # Créer la nouvelle carte RFID
                    RFIDCard.objects.create(
                        utilisateur=user,
                        card_uid=card_uid,
                        actif=True
                    )
                    messages.success(request, f'Carte RFID enregistrée pour {user.email}')
                    
            except Utilisateur.DoesNotExist:
                messages.error(request, 'Utilisateur non trouvé')
            except Exception as e:
                messages.error(request, f'Erreur lors de l\'enregistrement: {e}')
    
    # Liste des utilisateurs pour le formulaire
    users = Utilisateur.objects.filter(est_actif=True)
    return render(request, 'rfid/enregistrer_rfid.html', {'users': users})


def test_arduino_connection_view(request):
    """Vue pour tester la connexion Arduino"""
    if request.method == 'POST':
        try:
            handler = ArduinoRFIDHandler()
            if handler.connect():
                # Test de lecture pendant 5 secondes
                import time
                start_time = time.time()
                card_detected = False
                card_uid = None
                
                while time.time() - start_time < 5:
                    uid = handler.read_card_uid()
                    if uid:
                        card_detected = True
                        card_uid = uid
                        break
                    time.sleep(0.1)
                
                handler.disconnect()
                
                if card_detected:
                    return JsonResponse({
                        'success': True,
                        'message': f'Carte détectée: {card_uid}',
                        'card_uid': card_uid
                    })
                else:
                    return JsonResponse({
                        'success': False,
                        'message': 'Aucune carte détectée dans les 5 secondes'
                    })
            else:
                return JsonResponse({
                    'success': False,
                    'message': 'Impossible de se connecter à Arduino'
                })
                
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Erreur: {str(e)}'
            })
    
    return render(request, 'rfid/test_arduino.html')


def rfid_dashboard(request):
    """Tableau de bord pour la gestion RFID"""
    # Statistiques RFID
    total_cards = RFIDCard.objects.count()
    active_cards = RFIDCard.objects.filter(actif=True).count()
    recent_auths = HistoriqueAuthentification.objects.filter(
        type_auth=HistoriqueAuthentification.TypeAuth.NFC_CARTE
    ).order_by('-date_heure_acces')[:10]
    
    context = {
        'total_cards': total_cards,
        'active_cards': active_cards,
        'recent_auths': recent_auths,
    }
    
    return render(request, 'rfid/rfid_dashboard.html', context) 

@staff_member_required
def scan_rfid_uid(request):
    try:
        port = request.GET.get('port', 'COM6') # Port par défaut mis à jour
        baudrate = 9600
        import serial.tools.list_ports
        available_ports = [p.device for p in serial.tools.list_ports.comports()]
        if port not in available_ports:
            return JsonResponse({
               'success': False, 
               'error': f"Port {port} non disponible. Ports disponibles: {available_ports}"
            })
        ser = serial.Serial(port, baudrate, timeout=5)
        time.sleep(2)
        uid = None
        start = time.time()
        while time.time() - start < 10:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if "card_uid" in line:
                    try:
                        data = json.loads(line)
                        uid = data.get("card_uid")
                    except Exception:
                        pass
                    break
            time.sleep(0.1)
        ser.close()
        if uid:
            return JsonResponse({'success': True, 'uid': uid})
        else:
            return JsonResponse({'success': False, 'error': "Aucune carte détectée"})
    except PermissionError as e:
        return JsonResponse({
           'success': False, 
           'error': f"Erreur de permission pour le port {port}. Vérifiez que le port n'est pas utilisé par un autre programme."
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

def scan_rfid_admin_metier(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
    try:
        port = request.GET.get('port', 'COM6') # Port par défaut mis à jour
        baudrate = 9600
        ser = serial.Serial(port, baudrate, timeout=5)
        time.sleep(2)
        uid = None
        start = time.time()
        while time.time() - start < 10:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8').strip()
                if "card_uid" in line:
                    try:
                        data = json.loads(line)
                        uid = data.get("card_uid")
                    except Exception:
                        pass
                    break
            time.sleep(0.1)
        ser.close()
        if uid:
            return JsonResponse({'success': True, 'uid': uid})
        else:
            return JsonResponse({'success': False, 'error': "Aucune carte détectée"})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}) 