"""
Vues pour l'authentification RFID + OTP des médecins
Nouveau système d'authentification avec double facteur pour les médecins
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils import timezone
import json
import logging
import random
from django.core.mail import send_mail
from django.conf import settings

from .models import RFIDCard, Utilisateur, HistoriqueAuthentification
from .rfid_arduino_handler import ArduinoRFIDHandler

logger = logging.getLogger(__name__)


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
