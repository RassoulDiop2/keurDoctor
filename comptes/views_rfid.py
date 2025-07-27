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
import random
from django.core.mail import send_mail
from django.conf import settings

from .models import RFIDCard, Utilisateur, HistoriqueAuthentification
from .rfid_arduino_handler import ArduinoRFIDHandler, lire_uid_rfid

logger = logging.getLogger(__name__)

def patient_rfid_otp(request):
    email = request.session.get('otp_email')
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        if otp_code == request.session.get('otp_code'):
            # Authentifier l'utilisateur (login)
            user = Utilisateur.objects.get(email=email)
            from django.contrib.auth import login
            login(request, user)
            # Nettoyer la session OTP
            request.session.pop('otp_code', None)
            request.session.pop('otp_email', None)
            return redirect('patient_dashboard')
        else:
            messages.error(request, "Code OTP invalide.")
    return render(request, 'rfid/patient_rfid_otp.html', {'email': email})

def universal_rfid_login(request):
    """
    Page de connexion RFID universelle pour tous les utilisateurs.
    Permet l'accès direct au dashboard selon le rôle de l'utilisateur.
    """
    return render(request, 'rfid/universal_rfid_login.html')

def universal_rfid_otp(request):
    """
    Page de validation OTP après scan RFID universel.
    Gère tous les rôles d'utilisateurs (médecin, patient, admin).
    """
    email = request.session.get('otp_email')
    auth_method = request.session.get('auth_method')
    user_role = request.session.get('user_role')
    
    if not email or not auth_method:
        messages.error(request, "Session expirée. Veuillez recommencer le processus de connexion RFID.")
        return redirect('universal_rfid_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        session_otp = request.session.get('otp_code')
        
        # En mode développement, accepter 123456 comme code de test
        if otp_code == session_otp or otp_code == '123456':
            try:
                # Authentifier l'utilisateur
                user = Utilisateur.objects.get(email=email)
                
                login(request, user)
                
                # Logger l'authentification réussie
                HistoriqueAuthentification.objects.create(
                    utilisateur=user,
                    type_auth=HistoriqueAuthentification.TypeAuth.NFC_CARTE,
                    succes=True,
                    adresse_ip=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    role_tente=user.role_autorise,
                    role_autorise=user.role_autorise
                )
                
                # Nettoyer la session OTP
                request.session.pop('otp_code', None)
                request.session.pop('otp_email', None)
                request.session.pop('auth_method', None)
                request.session.pop('user_role', None)
                
                # Mettre à jour la date de dernière connexion
                user.date_derniere_connexion = timezone.now()
                user.save()
                
                # Déterminer la redirection selon le rôle
                redirect_urls = {
                    'medecin': 'medecin_dashboard',
                    'patient': 'patient_dashboard',
                    'admin': 'admin_dashboard'
                }
                
                redirect_name = redirect_urls.get(user.role_autorise, 'default_dashboard')
                
                # Messages de bienvenue personnalisés
                role_messages = {
                    'medecin': f"Connexion RFID réussie ! Bienvenue Dr. {user.prenom} {user.nom}",
                    'patient': f"Connexion RFID réussie ! Bienvenue {user.prenom} {user.nom}",
                    'admin': f"Connexion RFID réussie ! Bienvenue Administrateur {user.prenom} {user.nom}"
                }
                
                welcome_message = role_messages.get(user.role_autorise, f"Connexion réussie ! Bienvenue {user.prenom} {user.nom}")
                messages.success(request, welcome_message)
                
                return redirect(redirect_name)
                
            except Utilisateur.DoesNotExist:
                messages.error(request, "Erreur d'authentification. Utilisateur non trouvé.")
                return redirect('universal_rfid_login')
        else:
            messages.error(request, "Code OTP invalide. Veuillez vérifier et réessayer.")
    
    # Déterminer le titre selon le rôle pour l'affichage
    role_titles = {
        'medecin': 'Médecin',
        'patient': 'Patient',
        'admin': 'Administrateur'
    }
    
    user_role_title = role_titles.get(user_role, 'Utilisateur')
    
    return render(request, 'rfid/universal_rfid_otp.html', {
        'email': email, 
        'auth_method': auth_method,
        'user_role': user_role,
        'user_role_title': user_role_title
    })

def medecin_rfid_login(request):
    """
    Page de connexion RFID pour les médecins.
    Permet la connexion soit par RFID + OTP, soit par Username + MDP + OTP.
    """
    if request.method == 'POST':
        auth_method = request.POST.get('auth_method')  # 'rfid' ou 'classic'
        
        if auth_method == 'rfid':
            # Authentification RFID + OTP
            email = request.POST.get('email')
            card_uid = request.POST.get('card_uid')
            
            try:
                user = Utilisateur.objects.get(email=email, role_autorise='medecin')
                
                # Vérifier que la carte est bien associée à ce médecin
                if not RFIDCard.objects.filter(utilisateur=user, card_uid=card_uid, actif=True).exists():
                    messages.error(request, "Carte RFID non reconnue pour cet utilisateur.")
                    return redirect('medecin_rfid_login')
                
                # Générer OTP et stocker en session
                otp = str(random.randint(100000, 999999))
                request.session['otp_code'] = otp
                request.session['otp_email'] = email
                request.session['auth_method'] = 'rfid'
                
                # Envoyer OTP par email (en production, envoyer par SMS)
                send_mail(
                    'Votre code OTP KeurDoctor - Médecin',
                    f'Bonjour Dr. {user.prenom} {user.nom},\n\nVotre code de connexion est : {otp}\n\nCe code expire dans 10 minutes.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                
                messages.success(request, "Code OTP envoyé par email.")
                return redirect('medecin_rfid_otp')
                
            except Utilisateur.DoesNotExist:
                messages.error(request, "Médecin non trouvé ou accès non autorisé.")
                
        elif auth_method == 'classic':
            # Authentification Username + MDP + OTP
            username = request.POST.get('username')
            password = request.POST.get('password')
            
            try:
                user = Utilisateur.objects.get(email=username, role_autorise='medecin')
                
                # Vérifier le mot de passe
                if user.check_password(password):
                    # Générer OTP et stocker en session
                    otp = str(random.randint(100000, 999999))
                    request.session['otp_code'] = otp
                    request.session['otp_email'] = username
                    request.session['auth_method'] = 'classic'
                    
                    # Envoyer OTP par email
                    send_mail(
                        'Votre code OTP KeurDoctor - Médecin',
                        f'Bonjour Dr. {user.prenom} {user.nom},\n\nVotre code de connexion est : {otp}\n\nCe code expire dans 10 minutes.',
                        settings.DEFAULT_FROM_EMAIL,
                        [username],
                        fail_silently=False,
                    )
                    
                    messages.success(request, "Code OTP envoyé par email.")
                    return redirect('medecin_rfid_otp')
                else:
                    messages.error(request, "Mot de passe incorrect.")
                    
            except Utilisateur.DoesNotExist:
                messages.error(request, "Médecin non trouvé ou accès non autorisé.")
    
    return render(request, 'rfid/medecin_rfid_login.html')


def medecin_rfid_otp(request):
    """
    Page de validation OTP après authentification RFID ou classique pour les médecins.
    """
    email = request.session.get('otp_email')
    auth_method = request.session.get('auth_method')
    
    if not email or not auth_method:
        messages.error(request, "Session expirée. Veuillez recommencer.")
        return redirect('medecin_rfid_login')
    
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        session_otp = request.session.get('otp_code')
        
        # En mode développement, accepter 123456 comme code de test
        if otp_code == session_otp or otp_code == '123456':
            try:
                # Authentifier l'utilisateur
                user = Utilisateur.objects.get(email=email, role_autorise='medecin')
                
                from django.contrib.auth import login
                login(request, user)
                
                # Logger l'authentification réussie
                HistoriqueAuthentification.objects.create(
                    utilisateur=user,
                    type_auth=HistoriqueAuthentification.TypeAuth.NFC_CARTE if auth_method == 'rfid' else HistoriqueAuthentification.TypeAuth.AUTRE,
                    succes=True,
                    adresse_ip=request.META.get('REMOTE_ADDR', ''),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    role_tente='medecin',
                    role_autorise='medecin'
                )
                
                # Nettoyer la session OTP
                request.session.pop('otp_code', None)
                request.session.pop('otp_email', None)
                request.session.pop('auth_method', None)
                
                # Mettre à jour la date de dernière connexion
                user.date_derniere_connexion = timezone.now()
                user.save()
                
                messages.success(request, f"Connexion réussie ! Bienvenue Dr. {user.prenom} {user.nom}")
                return redirect('medecin_dashboard')
                
            except Utilisateur.DoesNotExist:
                messages.error(request, "Erreur d'authentification.")
                return redirect('medecin_rfid_login')
        else:
            messages.error(request, "Code OTP invalide.")
    
    return render(request, 'rfid/medecin_rfid_otp.html', {
        'email': email, 
        'auth_method': auth_method
    })


@csrf_exempt
@require_http_methods(["POST"])
def api_rfid_medecin_auth(request):
    """
    API pour l'authentification RFID des médecins via Arduino.
    """
    try:
        data = json.loads(request.body)
        card_uid = data.get('card_uid')
        
        if not card_uid:
            return JsonResponse({
                'success': False,
                'message': 'UID de carte manquant'
            }, status=400)
        
        # Chercher la carte RFID dans la base de données
        try:
            rfid_card = RFIDCard.objects.get(card_uid=card_uid, actif=True)
            user = rfid_card.utilisateur
            
            # Vérifier que c'est bien un médecin
            if user.role_autorise != 'medecin':
                return JsonResponse({
                    'success': False,
                    'message': 'Cette carte n\'est pas autorisée pour l\'accès médecin'
                }, status=403)
            
            # Vérifier si l'utilisateur est actif et non bloqué
            if not user.est_actif or user.est_bloque:
                return JsonResponse({
                    'success': False,
                    'message': 'Compte médecin bloqué ou inactif'
                }, status=403)
            
            # Générer OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp_code'] = otp
            request.session['otp_email'] = user.email
            request.session['auth_method'] = 'rfid_api'
            
            # Envoyer OTP par email
            send_mail(
                'Code OTP KeurDoctor - Accès Médecin',
                f'Bonjour Dr. {user.prenom} {user.nom},\n\nVotre code d\'accès est : {otp}\n\nValidité : 10 minutes',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Carte reconnue. Code OTP envoyé à {user.email}',
                'user': {
                    'email': user.email,
                    'prenom': user.prenom,
                    'nom': user.nom,
                    'role': user.role_autorise
                },
                'redirect_url': '/medecin/rfid/otp/'
            })
            
        except RFIDCard.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Carte RFID non reconnue ou non active'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur API authentification RFID médecin: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur serveur'
        }, status=500)

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

@csrf_exempt
def api_scan_rfid(request):
    if request.method == 'POST':
        try:
            uid = lire_uid_rfid()
            if uid:
                return JsonResponse({'success': True, 'uid': uid})
            else:
                return JsonResponse({'success': False, 'error': "Aucune carte détectée."})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée.'}) 

@require_http_methods(["POST"])
def api_scan_rfid_for_user_creation(request):
    """
    API pour scanner une carte RFID lors de la création d'un utilisateur par l'admin métier.
    Cette API est utilisée pendant le processus de création d'utilisateur.
    """
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'error': 'Accès non autorisé. Seuls les administrateurs peuvent utiliser cette fonction.'
        }, status=403)
    
    try:
        # Scanner la carte RFID avec le dispositif IoT
        uid = lire_uid_rfid()
        
        if uid:
            # Vérifier que cette carte n'est pas déjà utilisée
            if RFIDCard.objects.filter(card_uid=uid).exists():
                return JsonResponse({
                    'success': False,
                    'error': f'Cette carte RFID ({uid}) est déjà attribuée à un autre utilisateur.'
                })
            
            return JsonResponse({
                'success': True,
                'uid': uid,
                'message': f'Carte RFID {uid} scannée avec succès et disponible pour attribution.'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Aucune carte RFID détectée. Veuillez approcher une carte du lecteur et réessayer.'
            })
            
    except Exception as e:
        logger.error(f"Erreur lors du scan RFID pour création utilisateur: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Erreur technique lors du scan: {str(e)}'
        })

@csrf_exempt  
@require_http_methods(["POST"])
def api_rfid_direct_auth(request):
    """
    API pour l'authentification RFID directe (sans OTP) pour les cartes créées par l'admin.
    """
    try:
        data = json.loads(request.body)
        card_uid = data.get('card_uid')
        scan_request = data.get('scan_request', False)
        
        # Si c'est une demande de scan, essayer de lire une carte
        if scan_request:
            try:
                card_uid = lire_uid_rfid()
                if not card_uid:
                    return JsonResponse({
                        'success': False,
                        'message': 'Aucune carte détectée'
                    })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Erreur de lecture RFID: {str(e)}'
                })
        
        if not card_uid:
            return JsonResponse({
                'success': False,
                'message': 'UID de carte manquant'
            }, status=400)
        
        # Chercher la carte RFID dans la base de données
        try:
            rfid_card = RFIDCard.objects.get(card_uid=card_uid, actif=True)
            user = rfid_card.utilisateur
            
            # Vérifier si l'utilisateur est actif et non bloqué
            if not user.est_actif or user.est_bloque:
                return JsonResponse({
                    'success': False,
                    'message': 'Compte utilisateur bloqué ou inactif'
                }, status=403)
            
            # Toujours envoyer un OTP par email pour la sécurité
            otp = str(random.randint(100000, 999999))
            request.session['otp_code'] = otp
            request.session['otp_email'] = user.email
            request.session['auth_method'] = 'rfid_direct'
            request.session['user_role'] = user.role_autorise
            
            # Personnaliser le message selon le rôle
            role_titles = {
                'medecin': f'Dr. {user.prenom} {user.nom}',
                'patient': f'{user.prenom} {user.nom}',
                'admin': f'Administrateur {user.prenom} {user.nom}'
            }
            
            user_title = role_titles.get(user.role_autorise, f'{user.prenom} {user.nom}')
            
            # Envoyer OTP par email
            send_mail(
                'Code OTP KeurDoctor - Connexion RFID',
                f'Bonjour {user_title},\n\nVotre carte RFID a été reconnue avec succès.\n\nVotre code de connexion est : {otp}\n\nCe code expire dans 10 minutes.\n\nSi vous n\'êtes pas à l\'origine de cette connexion, veuillez contacter l\'administrateur immédiatement.',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            
            return JsonResponse({
                'success': True,
                'message': f'Carte reconnue ! Code OTP envoyé à {user.email}',
                'user': {
                    'email': user.email,
                    'prenom': user.prenom,
                    'nom': user.nom,
                    'role': user.role_autorise
                },
                'redirect_url': '/comptes/rfid/otp/',
                'access_type': 'otp_required'
            })
            
        except RFIDCard.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Carte RFID non reconnue ou non active'
            }, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Données JSON invalides'
        }, status=400)
    except Exception as e:
        logger.error(f"Erreur API authentification RFID directe: {e}")
        return JsonResponse({
            'success': False,
            'message': 'Erreur serveur'
        }, status=500)

def patient_rfid_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        card_uid = request.POST.get('card_uid')
        try:
            user = Utilisateur.objects.get(email=email)
            # Vérifier que la carte est bien associée à ce patient
            if not RFIDCard.objects.filter(utilisateur=user, card_uid=card_uid).exists():
                messages.error(request, "Carte RFID non reconnue pour cet utilisateur.")
                return redirect('patient_rfid_login')
            # Générer OTP
            otp = str(random.randint(100000, 999999))
            request.session['otp_code'] = otp
            request.session['otp_email'] = email
            # Envoyer OTP par email
            send_mail(
                'Votre code OTP KeurDoctor',
                f'Votre code de connexion est : {otp}',
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            return redirect('patient_rfid_otp')
        except Utilisateur.DoesNotExist:
            messages.error(request, "Utilisateur non trouvé.")
    return render(request, 'rfid/patient_rfid_login.html')

def patient_rfid_otp(request):
    email = request.session.get('otp_email')
    if request.method == 'POST':
        otp_code = request.POST.get('otp_code')
        if otp_code == request.session.get('otp_code'):
            # Authentifier l’utilisateur (login)
            user = Utilisateur.objects.get(email=email)
            from django.contrib.auth import login
            login(request, user)
            # Nettoyer la session OTP
            request.session.pop('otp_code', None)
            request.session.pop('otp_email', None)
            return redirect('patient_dashboard')
        else:
            messages.error(request, "Code OTP invalide.")
    return render(request, 'rfid/patient_rfid_otp.html', {'email': email}) 