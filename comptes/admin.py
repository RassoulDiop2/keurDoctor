from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import (Utilisateur,
                     Medecin,
                     Patient,
                     Administrateur,
                     RendezVous,
                     DossierMedical,
                     HistoriqueAuthentification,
                     HistoriqueJournalisation,
                     LicenceAcceptation)

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
                'url': '/admin/users/',
                'label': 'Gestion des utilisateurs personnalisée',
                'icon': 'fas fa-users',
                'target': '_blank',
            },
            {
                'url': '/admin/securite/',
                'label': 'Gestion de la sécurité personnalisée',
                'icon': 'fas fa-shield-alt',
                'target': '_blank',
            },
        ]
        extra_context['liens_rapides_html'] = format_html(
            '<div style="margin: 1em 0; padding: 1em; background: #f8f9fa; border-radius: 8px;">'
            '<h4>Liens rapides</h4>'
            '<ul style="list-style:none; padding-left:0;">'
            '<li><a href="/admin/users/" target="_blank"><i class="fas fa-users"></i> Gestion des utilisateurs personnalisée</a></li>'
            '<li><a href="/admin/securite/" target="_blank"><i class="fas fa-shield-alt"></i> Gestion de la sécurité personnalisée</a></li>'
            '</ul>'
            '</div>'
        )
        return super().index(request, extra_context=extra_context)

# Remplacer l'admin par défaut par le custom
admin.site = CustomAdminSite()

admin.site.register(Utilisateur)
admin.site.register(Medecin)
admin.site.register(Patient)
admin.site.register(Administrateur)
admin.site.register(RendezVous)
admin.site.register(DossierMedical)
admin.site.register(HistoriqueAuthentification)
admin.site.register(HistoriqueJournalisation)
admin.site.register(LicenceAcceptation)

