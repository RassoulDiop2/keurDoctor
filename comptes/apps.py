from django.apps import AppConfig


class ComptesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comptes'
    
    def ready(self):
        """Charge les signaux automatiques lors du démarrage de l'application"""
        try:
            import comptes.keycloak_auto_sync  # Import des signaux automatiques
            print("✅ Synchronisation automatique Keycloak activée")
        except ImportError as e:
            print(f"⚠️ Erreur chargement synchronisation automatique: {e}")
