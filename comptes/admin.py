from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.contrib.auth.admin import UserAdmin
from .models import (Utilisateur,
                     MedecinNew,
                     PatientNew,
                     RendezVous,
                     HistoriqueAuthentification,
                     HistoriqueJournalisation,
                     LicenceAcceptation,
                     AlerteSecurite,
                     SpecialiteMedicale,
                     Consultation,
                     Prescription,
                     DossierMedical,
                     DocumentMedical,
                     AuditLog,
                     RFIDCard)
from django.utils import timezone
from django.utils.safestring import mark_safe
from django import forms
from django.contrib.auth.models import Group

class UtilisateurCreationForm(forms.ModelForm):
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('medecin', 'Médecin'),
        ('patient', 'Patient'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, label="Rôle")

    class Meta:
        model = Utilisateur
        fields = ('email', 'prenom', 'nom', 'role', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data['role']
        # Ajout explicite des champs prénom et nom
        user.prenom = self.cleaned_data['prenom']
        user.nom = self.cleaned_data['nom']
        if commit:
            user.save()
            group_map = {
                'admin': 'administrateurs',
                'medecin': 'médecins',
                'patient': 'patients',
            }
            group_name = group_map[role]
            group, _ = Group.objects.get_or_create(name=group_name)
            user.groups.clear()
            user.groups.add(group)
            # Met à jour le champ role_autorise aussi
            user.role_autorise = role
            user.save()
        return user

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
            'fields': ('email', 'prenom', 'nom', 'role', 'password1', 'password2'),
        }),
    )

    add_form = UtilisateurCreationForm

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj is None:
            # Masquer le champ groupes à la création
            if 'groups' in form.base_fields:
                form.base_fields['groups'].widget = forms.HiddenInput()
        return form

class MedecinAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'specialite', 'numero_praticien')
    search_fields = ('utilisateur__email', 'utilisateur__prenom', 'utilisateur__nom', 'specialite')
    list_filter = ('specialite',)

class PatientAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_naissance', 'numero_dossier')
    search_fields = ('utilisateur__email', 'utilisateur__prenom', 'utilisateur__nom', 'numero_dossier')
    list_filter = ('date_naissance',)

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

class RFIDScanWidget(admin.widgets.AdminTextInputWidget):
    class Media:
        js = ('js/rfid_scan.js',)

    def render(self, name, value, attrs=None, renderer=None):
        html = super().render(name, value, attrs, renderer)
        scan_btn = f'<button type="button" class="button scan-rfid-btn" data-field="{name}">Scanner</button>'
        return mark_safe(html + scan_btn)

@admin.register(PatientNew)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'date_naissance', 'medecin_traitant')
    fields = ('utilisateur', 'numero_securite_sociale', 'date_naissance', 'telephone', 'adresse', 'medecin_traitant', 'groupe_sanguin', 'allergies_connues')
    search_fields = ('utilisateur__email', 'utilisateur__nom', 'utilisateur__prenom', 'numero_securite_sociale')
    list_filter = ('medecin_traitant', 'groupe_sanguin')

@admin.register(MedecinNew)
class MedecinAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'numero_ordre', 'patients_actifs', 'accepte_nouveaux_patients')
    fields = ('utilisateur', 'numero_ordre', 'specialites', 'telephone_cabinet', 'adresse_cabinet', 'horaires_consultation', 'tarif_consultation', 'accepte_nouveaux_patients')
    search_fields = ('utilisateur__email', 'utilisateur__nom', 'utilisateur__prenom', 'numero_ordre')
    list_filter = ('specialites', 'accepte_nouveaux_patients')
    filter_horizontal = ('specialites',)

# Enregistrer les nouveaux modèles médicaux
@admin.register(SpecialiteMedicale)
class SpecialiteMedicaleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)

@admin.register(RendezVous)
class RendezVousAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_rdv', 'type_rdv', 'statut')
    list_filter = ('statut', 'type_rdv', 'medecin')
    search_fields = ('patient__utilisateur__nom', 'patient__utilisateur__prenom', 'medecin__utilisateur__nom')
    date_hierarchy = 'date_rdv'

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('patient', 'medecin', 'date_consultation', 'motif_consultation')
    list_filter = ('medecin', 'date_consultation')
    search_fields = ('patient__utilisateur__nom', 'motif_consultation', 'diagnostic')
    date_hierarchy = 'date_consultation'

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'medicament', 'date_prescription')
    list_filter = ('date_prescription',)
    search_fields = ('medicament', 'consultation__patient__utilisateur__nom')

@admin.register(DossierMedical)
class DossierMedicalAdmin(admin.ModelAdmin):
    list_display = ('patient', 'statut', 'date_creation', 'date_mise_a_jour')
    list_filter = ('statut', 'date_creation')
    search_fields = ('patient__utilisateur__nom', 'patient__utilisateur__prenom')

@admin.register(DocumentMedical)
class DocumentMedicalAdmin(admin.ModelAdmin):
    list_display = ('titre', 'type_document', 'dossier', 'date_creation')
    list_filter = ('type_document', 'date_creation')
    search_fields = ('titre', 'dossier__patient__utilisateur__nom')

# Enregistrer les modèles avec leurs configurations personnalisées
admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.register(LicenceAcceptation)
admin.site.register(HistoriqueAuthentification, HistoriqueAuthentificationAdmin)
admin.site.register(HistoriqueJournalisation, HistoriqueJournalisationAdmin)
admin.site.register(AlerteSecurite, AlerteSecuriteAdmin)

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('utilisateur', 'type_action', 'niveau_risque', 'date_heure', 'adresse_ip')
    list_filter = ('type_action', 'niveau_risque', 'date_heure', 'est_suspect')
    search_fields = ('utilisateur__nom', 'utilisateur__email', 'description', 'adresse_ip')
    readonly_fields = ('date_heure', 'session_id')
    ordering = ['-date_heure']

@admin.register(RFIDCard)
class RFIDCardAdmin(admin.ModelAdmin):
    list_display = ('card_uid', 'utilisateur', 'actif', 'date_enregistrement')
    list_filter = ('actif', 'date_enregistrement')
    search_fields = ('card_uid', 'utilisateur__nom', 'utilisateur__email')
    readonly_fields = ('date_enregistrement',)


