from functools import wraps
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
import logging

logger = logging.getLogger(__name__)


def role_required(role):
    """
    Décorateur pour vérifier qu'un utilisateur a un rôle spécifique
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('oidc_authentication_init')
            
            # Vérifier si l'utilisateur a le rôle requis
            user_groups = [group.name.lower() for group in request.user.groups.all()]
            
            # Support des anciens et nouveaux noms de groupes
            role_variants = {
                'admin': ['admin', 'administrateurs'],
                'medecin': ['medecin', 'médecins'],
                'patient': ['patient', 'patients'],
            }
            
            allowed_groups = role_variants.get(role, [role])
            has_required_role = any(group in user_groups for group in allowed_groups)
            
            # Debug logging
            logger.info(f"Role check for user {request.user.username}: "
                       f"required_role='{role}', user_groups={user_groups}, "
                       f"allowed_groups={allowed_groups}, has_access={has_required_role}")
            
            if not has_required_role:
                logger.warning(f"Access denied for user {request.user.username} to role {role}")
                raise PermissionDenied(f"Accès refusé. Rôle requis: {role}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def any_role_required(*roles):
    """
    Décorateur pour vérifier qu'un utilisateur a au moins un des rôles spécifiés
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('oidc_authentication_init')
            
            user_groups = [group.name.lower() for group in request.user.groups.all()]
            
            # Support des anciens et nouveaux noms de groupes
            role_variants = {
                'admin': ['admin', 'administrateurs'],
                'medecin': ['medecin', 'médecins'],
                'patient': ['patient', 'patients'],
            }
            
            # Vérifier si l'utilisateur a au moins un des rôles requis
            has_role = False
            for role in roles:
                allowed_groups = role_variants.get(role, [role])
                if any(group in user_groups for group in allowed_groups):
                    has_role = True
                    break
            
            if not has_role:
                raise PermissionDenied(f"Accès refusé. Rôles requis: {', '.join(roles)}")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
