from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Utilisateur, Medecin, Patient
import logging

logger = logging.getLogger(__name__)


def role_required(role):
    """Décorateur pour vérifier le rôle de l'utilisateur"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('home')
            # Vérifier si l'utilisateur est bloqué
            if hasattr(request.user, 'est_bloque') and request.user.est_bloque:
                messages.error(request, f"Votre compte est bloqué: {request.user.raison_blocage}")
                return redirect('home')
            # Vérifier le rôle (accepte variantes de groupes)
            user_groups = [group.name.lower() for group in request.user.groups.all()]
            if role == 'admin':
                valid_groups = ['admin', 'administrateurs']
            elif role == 'medecin':
                valid_groups = ['medecin', 'medecins', 'médecins']
            elif role == 'patient':
                valid_groups = ['patient', 'patients']
            else:
                valid_groups = [role]
            if not any(g in user_groups for g in valid_groups):
                logger.warning(f"Tentative d'accès non autorisé: {request.user.email} - Rôle requis: {role}")
                messages.error(request, f"Accès refusé. Rôle {role} requis.")
                return HttpResponseForbidden("Accès non autorisé")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def any_role_required(*roles):
    """Décorateur pour vérifier que l'utilisateur a au moins un des rôles spécifiés"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('home')
            
            # Vérifier si l'utilisateur est bloqué
            if hasattr(request.user, 'est_bloque') and request.user.est_bloque:
                messages.error(request, f"Votre compte est bloqué: {request.user.raison_blocage}")
                return redirect('home')
            
            # Vérifier les rôles
            user_groups = [group.name.lower() for group in request.user.groups.all()]
            if not any(role in user_groups for role in roles):
                logger.warning(f"Tentative d'accès non autorisé: {request.user.email} - Rôles requis: {roles}")
                messages.error(request, f"Accès refusé. Rôles requis: {', '.join(roles)}")
                return HttpResponseForbidden("Accès non autorisé")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def medical_data_access_required(view_func):
    """Décorateur pour contrôler l'accès aux données médicales"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('home')
        
        # Vérifier si l'utilisateur est bloqué
        if hasattr(request.user, 'est_bloque') and request.user.est_bloque:
            messages.error(request, f"Votre compte est bloqué: {request.user.raison_blocage}")
            return redirect('home')
        
        # Seuls les médecins et admins peuvent accéder aux données médicales
        user_groups = [group.name.lower() for group in request.user.groups.all()]
        if 'medecin' not in user_groups and 'admin' not in user_groups:
            logger.warning(f"Tentative d'accès aux données médicales: {request.user.email}")
            messages.error(request, "Accès aux données médicales refusé. Rôle médecin ou admin requis.")
            return HttpResponseForbidden("Accès aux données médicales non autorisé")
        
        # Log de l'accès aux données médicales
        logger.info(f"Accès aux données médicales: {request.user.email} - {request.path}")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def patient_data_access_required(view_func):
    """Décorateur pour contrôler l'accès aux données d'un patient spécifique"""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('home')
        
        # Vérifier si l'utilisateur est bloqué
        if hasattr(request.user, 'est_bloque') and request.user.est_bloque:
            messages.error(request, f"Votre compte est bloqué: {request.user.raison_blocage}")
            return redirect('home')
        
        user_groups = [group.name.lower() for group in request.user.groups.all()]
        
        # Si c'est un patient, il ne peut voir que ses propres données
        if 'patient' in user_groups:
            patient_id = kwargs.get('patient_id')
            if patient_id and str(request.user.patient.id) != str(patient_id):
                logger.warning(f"Tentative d'accès aux données d'un autre patient: {request.user.email}")
                messages.error(request, "Vous ne pouvez accéder qu'à vos propres données.")
                return HttpResponseForbidden("Accès non autorisé")
        
        # Si c'est un médecin, vérifier qu'il a le droit d'accéder à ce patient
        elif 'medecin' in user_groups:
            # Ici vous pouvez ajouter une logique pour vérifier si le médecin
            # a une relation avec ce patient (rendez-vous, dossier médical, etc.)
            pass
        
        # Les admins ont accès à tout
        elif 'admin' not in user_groups:
            logger.warning(f"Tentative d'accès non autorisé aux données patient: {request.user.email}")
            messages.error(request, "Accès refusé.")
            return HttpResponseForbidden("Accès non autorisé")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def detecter_usurpation_role(view_func):
    """Décorateur pour détecter les tentatives d'usurpation de rôle"""
    def wrapper(request, *args, **kwargs):
        # Vérifier si un rôle est simulé dans la session
        role_simule = request.session.get('role_simule')
        
        if role_simule and role_simule != request.user.role_autorise:
            # Log de la tentative d'usurpation détectée
            from .models import AuditLog, AlerteSecurite
            
            AuditLog.log_action(
                utilisateur=request.user,
                type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
                description=f"Usurpation de rôle détectée: {request.user.role_autorise} → {role_simule}",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.CRITIQUE
            )
            
            # Créer une alerte de sécurité
            AlerteSecurite.objects.create(
                type_alerte='VIOLATION_SECURITE',
                utilisateur_concerne=request.user,
                details=f"Usurpation de rôle détectée: {request.user.role_autorise} → {role_simule}",
                niveau_urgence='CRITIQUE',
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Bloquer l'utilisateur automatiquement
            request.user.bloquer(f"Usurpation de rôle détectée: {request.user.role_autorise} → {role_simule}")
            
            # Nettoyer la session
            if 'role_simule' in request.session:
                del request.session['role_simule']
            
            return HttpResponseForbidden("🚨 ALERTE SÉCURITÉ: Tentative d'usurpation de rôle détectée. Votre compte a été bloqué.")
        
        return view_func(request, *args, **kwargs)
    return wrapper

def verifier_elevation_privileges(view_func):
    """Décorateur pour vérifier les élévations de privilèges"""
    def wrapper(request, *args, **kwargs):
        # Vérifier si l'utilisateur tente d'accéder à des fonctionnalités au-dessus de son niveau
        role_actuel = request.user.role_autorise
        url_path = request.path
        
        # Définir les niveaux d'accès requis
        niveaux_acces = {
            'patient': ['patient'],
            'medecin': ['patient', 'medecin'],
            'admin': ['patient', 'medecin', 'admin']
        }
        
        # Déterminer le niveau requis pour cette URL
        niveau_requis = 'patient'  # Par défaut
        if '/medecin/' in url_path:
            niveau_requis = 'medecin'
        elif '/admin/' in url_path or '/administration/' in url_path:
            niveau_requis = 'admin'
        
        # Vérifier si l'utilisateur a le niveau requis
        if role_actuel not in niveaux_acces.get(niveau_requis, []):
            # Log de la tentative d'élévation
            from .models import AuditLog, AlerteSecurite
            
            AuditLog.log_action(
                utilisateur=request.user,
                type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
                description=f"Tentative d'élévation de privilèges: {role_actuel} → {niveau_requis}",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.ELEVE
            )
            
            # Créer une alerte de sécurité
            AlerteSecurite.objects.create(
                type_alerte='TENTATIVE_ACCES_NON_AUTORISE',
                utilisateur_concerne=request.user,
                details=f"Tentative d'élévation de privilèges: {role_actuel} → {niveau_requis}",
                niveau_urgence='HAUTE',
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            return HttpResponseForbidden(f"❌ Accès refusé: Vous n'avez pas les privilèges requis ({niveau_requis})")
            
            return view_func(request, *args, **kwargs)
        return wrapper
