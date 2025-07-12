import logging
from django.utils.deprecation import MiddlewareMixin
from django.http import HttpResponseForbidden
from django.contrib import messages
from .models import AuditLog, AlerteSecurite
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """Middleware pour la sécurité et l'audit automatique"""
    
    def process_request(self, request):
        """Traite chaque requête pour la sécurité"""
        # Ignorer les requêtes statiques
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Log de la requête
        if hasattr(request, 'user') and request.user.is_authenticated:
            AuditLog.log_action(
                utilisateur=request.user,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description=f"Accès à {request.path}",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
        
        # Vérification des tentatives de connexion
        if request.path.startswith('/oidc/') and request.user.is_authenticated:
            self._verifier_tentatives_connexion(request)
        
        # Vérification des accès aux données sensibles
        if any(sensitive_path in request.path for sensitive_path in ['/patient/', '/medecin/', '/admin/']):
            self._verifier_acces_sensible(request)
        
        return None
    
    def _verifier_tentatives_connexion(self, request):
        """Vérifie les tentatives de connexion suspectes"""
        ip = request.META.get('REMOTE_ADDR', '')
        
        # Compter les tentatives de connexion depuis cette IP
        tentatives_recentes = AuditLog.objects.filter(
            adresse_ip=ip,
            type_action=AuditLog.TypeAction.CONNEXION,
            date_heure__gte=timezone.now() - timedelta(minutes=15)
        ).count()
        
        if tentatives_recentes > 10:
            # Créer une alerte de sécurité seulement si l'utilisateur est authentifié
            if request.user.is_authenticated:
                AlerteSecurite.objects.create(
                    type_alerte='VIOLATION_SECURITE',
                    utilisateur_concerne=request.user,
                    details=f"Trop de tentatives de connexion depuis l'IP {ip}",
                    niveau_urgence='HAUTE',
                    adresse_ip=ip
                )
            
            logger.warning(f"Trop de tentatives de connexion depuis {ip}")
            return HttpResponseForbidden("Trop de tentatives de connexion")
    
    def _verifier_acces_sensible(self, request):
        """Vérifie les accès aux données sensibles"""
        if not request.user.is_authenticated:
            return None
        
        # Log de l'accès aux données sensibles
        AuditLog.log_action(
            utilisateur=request.user,
            type_action=AuditLog.TypeAction.ACCES_MEDICAL,
            description=f"Accès aux données sensibles: {request.path}",
            request=request,
            niveau_risque=AuditLog.NiveauRisque.ELEVE
        )
        
        # Vérifier les permissions
        user_groups = [group.name.lower() for group in request.user.groups.all()]
        
        if '/patient/' in request.path and 'patient' not in user_groups and 'admin' not in user_groups:
            AuditLog.log_action(
                utilisateur=request.user,
                type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
                description=f"Tentative d'accès non autorisé aux données patient",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.CRITIQUE
            )
            
            messages.error(request, "Accès non autorisé aux données patient")
            return HttpResponseForbidden("Accès non autorisé")
    
    def process_response(self, request, response):
        """Traite la réponse pour l'audit"""
        # Ajouter des headers de sécurité
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Log des erreurs 4xx et 5xx
        if response.status_code >= 400:
            AuditLog.log_action(
                utilisateur=getattr(request, 'user', None),
                type_action=AuditLog.TypeAction.VIOLATION_SECURITE,
                description=f"Erreur {response.status_code} sur {request.path}",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.MOYEN
            )
        
        return response


class AuditMiddleware(MiddlewareMixin):
    """Middleware pour l'audit automatique"""
    
    def process_request(self, request):
        """Audit automatique des requêtes"""
        # Ignorer les requêtes statiques
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Log de base pour toutes les requêtes authentifiées
        if hasattr(request, 'user') and request.user.is_authenticated:
            AuditLog.log_action(
                utilisateur=request.user,
                type_action=AuditLog.TypeAction.LECTURE_DONNEES,
                description=f"Requête: {request.method} {request.path}",
                request=request,
                niveau_risque=AuditLog.NiveauRisque.FAIBLE
            )
        
        return None 