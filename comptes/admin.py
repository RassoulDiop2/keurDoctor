from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin
from .models import (Utilisateur,
                     Medecin,
                     Patient,
                     Administrateur,
                     RendezVous,
                     DossierMedical,
                     HistoriqueAuthentification,
                     HistoriqueJournalisation,
                     LicenceAcceptation,
                     AlerteSecurite)
from django.utils import timezone

class UtilisateurAdmin(UserAdmin):
    """Configuration admin personnalisée pour le modèle Utilisateur"""
    model = Utilisateur
    list_display = ('email', 'prenom', 'nom', 'role_autorise', 'est_actif', 'est_bloque', 'date_creation')
    list_filter = ('est_actif', 'est_bloque', 'role_autorise', 'date_creation')
    search_fields = ('email', 'prenom', 'nom')
    ordering = ('-date_creation',)
    readonly_fields = ('date_creation', 'date_derniere_connexion', 'keycloak_id')
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('prenom', 'nom')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Sécurité KeurDoctor', {
            'fields': ('role_autorise', 'est_bloque', 'date_blocage', 'raison_blocage', 'tentatives_connexion_incorrectes'),
        }),
        ('Informations système', {'fields': ('last_login', 'date_creation', 'date_derniere_connexion', 'keycloak_id')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'prenom', 'nom', 'password1', 'password2', 'role_autorise'),
        }),
    )

class MedecinAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'specialite', 'numero_praticien')
    search_fields = ('utilisateur__email', 'utilisateur__prenom', 'utilisateur__nom', 'specialite')
    list_filter = ('specialite',)

class PatientAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_naissance', 'numero_dossier')
    search_fields = ('utilisateur__email', 'utilisateur__prenom', 'utilisateur__nom', 'numero_dossier')
    list_filter = ('date_naissance',)

class AdministrateurAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'niveau_acces')
    list_filter = ('niveau_acces',)

class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('medecin', 'patient', 'date_heure', 'statut')
    list_filter = ('statut', 'date_heure')
    search_fields = ('medecin__utilisateur__email', 'patient__utilisateur__email')
    date_hierarchy = 'date_heure'

class DossierMedicalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin_referent', 'date_creation')
    list_filter = ('date_creation',)
    search_fields = ('patient__utilisateur__email', 'medecin_referent__utilisateur__email')
    date_hierarchy = 'date_creation'

class HistoriqueAuthentificationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_auth', 'date_heure_acces', 'succes', 'adresse_ip')
    list_filter = ('type_auth', 'succes', 'date_heure_acces')
    search_fields = ('utilisateur__email', 'adresse_ip')
    date_hierarchy = 'date_heure_acces'
    readonly_fields = ('date_heure_acces',)

class HistoriqueJournalisationAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'action', 'type_evenement', 'date_heure')
    list_filter = ('type_evenement', 'date_heure')
    search_fields = ('utilisateur__email', 'action', 'details')
    date_hierarchy = 'date_heure'
    readonly_fields = ('date_heure',)

class AlerteSecuriteAdmin(admin.ModelAdmin):
    list_display = ('type_alerte', 'utilisateur_concerne', 'niveau_urgence', 'est_lue', 'date_creation')
    list_filter = ('type_alerte', 'niveau_urgence', 'est_lue', 'date_creation')
    search_fields = ('utilisateur_concerne__email', 'details')
    date_hierarchy = 'date_creation'
    readonly_fields = ('date_creation',)
    actions = ['marquer_comme_lue']

    def marquer_comme_lue(self, request, queryset):
        updated = queryset.update(est_lue=True)
        self.message_user(request, f'{updated} alerte(s) marquée(s) comme lue(s).')
    marquer_comme_lue.short_description = "Marquer les alertes sélectionnées comme lues"

class CustomAdminSite(admin.AdminSite):
    site_header = 'Administration de KeurDoctor'
    site_title = 'KeurDoctor Admin'
    index_title = 'Tableau de bord administrateur'

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('liens-rapides/', self.admin_view(self.liens_rapides_view), name='liens_rapides'),
        ]
        return custom_urls + urls

    def liens_rapides_view(self, request):
        return admin.site.each_context(request)

    def index(self, request, extra_context=None):
        if extra_context is None:
            extra_context = {}
        extra_context['liens_rapides'] = [
            {
                'url': '/administration/',
                'label': 'Dashboard Administrateur',
                'icon': 'fas fa-tachometer-alt',
                'target': '_blank',
            },
            {
                'url': '/administration/securite/',
                'label': 'Gestion de la Sécurité',
                'icon': 'fas fa-shield-alt',
                'target': '_blank',
            },
            {
                'url': '/administration/users/',
                'label': 'Gestion des Utilisateurs',
                'icon': 'fas fa-users',
                'target': '_blank',
            },
        ]
        extra_context['liens_rapides_html'] = format_html(
            '<div style="margin: 1em 0; padding: 1em; background: #f8f9fa; border-radius: 8px;">'
            '<h4>Liens rapides KeurDoctor</h4>'
            '<ul style="list-style:none; padding-left:0;">'
            '<li><a href="/administration/" target="_blank"><i class="fas fa-tachometer-alt"></i> Dashboard Administrateur</a></li>'
            '<li><a href="/administration/securite/" target="_blank"><i class="fas fa-shield-alt"></i> Gestion de la Sécurité</a></li>'
            '<li><a href="/administration/users/" target="_blank"><i class="fas fa-users"></i> Gestion des Utilisateurs</a></li>'
            '</ul>'
            '</div>'
        )
        return super().index(request, extra_context=extra_context)

# Remplacer l'admin par défaut par le custom
admin.site = CustomAdminSite()

# Enregistrer les modèles avec leurs configurations personnalisées
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(Medecin, MedecinAdmin)
admin.site.register(Patient, PatientAdmin)
admin.site.register(Administrateur, AdministrateurAdmin)
admin.site.register(RendezVous, RendezVousAdmin)
admin.site.register(DossierMedical, DossierMedicalAdmin)
admin.site.register(HistoriqueAuthentification, HistoriqueAuthentificationAdmin)
admin.site.register(HistoriqueJournalisation, HistoriqueJournalisationAdmin)
admin.site.register(LicenceAcceptation)
admin.site.register(AlerteSecurite, AlerteSecuriteAdmin)


