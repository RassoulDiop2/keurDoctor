from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone
from django.core.exceptions import ValidationError
import uuid
from cryptography.fernet import Fernet
from django.conf import settings
import base64
import os
import logging

# Configuration du logger
logger = logging.getLogger(__name__)

class UtilisateurManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, prenom=None, nom=None, password=None, **extra_fields):
        if not email:
            raise ValueError("L'adresse email doit être renseignée")
        email = self.normalize_email(email)
        extra_fields.pop('username', None)  # On retire username si présent
        prenom = prenom or extra_fields.pop('prenom', '')
        nom = nom or extra_fields.pop('nom', '')
        user = self.model(email=email, prenom=prenom, nom=nom, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, prenom=None, nom=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('est_actif', True)
        extra_fields.pop('username', None)  # On retire username si présent

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superutilisateur doit avoir is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superutilisateur doit avoir is_superuser=True.')

        return self.create_user(email, prenom, nom, password, **extra_fields)


class Utilisateur(AbstractUser):
    username = None  # On désactive le champ username
    # password = None  # On retire cette ligne pour permettre la gestion du mot de passe

    keycloak_id = models.UUIDField(unique=True, db_index=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    prenom = models.CharField(max_length=100)
    nom = models.CharField(max_length=100)
    est_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_derniere_connexion = models.DateTimeField(null=True, blank=True)
    
    # Nouveaux champs de sécurité
    role_autorise = models.CharField(
        max_length=20, 
        choices=[
            ('admin', 'Administrateur'),
            ('medecin', 'Médecin'),
            ('patient', 'Patient'),
        ],
        null=True, 
        blank=True,
        help_text="Rôle autorisé pour cet utilisateur"
    )
    est_bloque = models.BooleanField(default=False, help_text="Utilisateur bloqué pour violation de sécurité")
    date_blocage = models.DateTimeField(null=True, blank=True, help_text="Date de blocage")
    raison_blocage = models.TextField(blank=True, help_text="Raison du blocage")
    tentatives_connexion_incorrectes = models.IntegerField(default=0, help_text="Nombre de tentatives de connexion incorrectes")
    derniere_tentative_incorrecte = models.DateTimeField(null=True, blank=True)
    bloque_par_admin = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='utilisateurs_bloques',
        help_text="Admin qui a bloqué cet utilisateur"
    )
    role_demande = models.CharField(
        max_length=20,
        choices=[
            ('admin', 'Administrateur'),
            ('medecin', 'Médecin'),
            ('patient', 'Patient'),
        ],
        null=True,
        blank=True,
        help_text="Rôle souhaité par l'utilisateur à l'inscription"
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['prenom', 'nom']

    objects = UtilisateurManager()

    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.email})"
    
    def bloquer(self, raison, admin_bloqueur=None):
        """Bloque l'utilisateur"""
        self.est_bloque = True
        self.date_blocage = timezone.now()
        self.raison_blocage = raison
        self.bloque_par_admin = admin_bloqueur
        self.save()
        
        # Créer une alerte admin
        AlerteSecurite.objects.create(
            type_alerte='BLOQUAGE_UTILISATEUR',
            utilisateur_concerne=self,
            details=f"Utilisateur bloqué: {raison}",
            niveau_urgence='HAUTE',
            admin_qui_a_bloque=admin_bloqueur
        )
    
    def debloquer(self, admin_debloqueur):
        """Débloque l'utilisateur"""
        self.est_bloque = False
        self.date_blocage = None
        self.raison_blocage = ""
        self.bloque_par_admin = None
        self.tentatives_connexion_incorrectes = 0
        self.derniere_tentative_incorrecte = None
        self.save()
        
        # Créer une alerte admin
        AlerteSecurite.objects.create(
            type_alerte='DEBLOQUAGE_UTILISATEUR',
            utilisateur_concerne=self,
            details=f"Utilisateur débloqué par {admin_debloqueur.email}",
            niveau_urgence='MOYENNE',
            admin_qui_a_bloque=admin_debloqueur
        )
    
    def incrementer_tentative_incorrecte(self):
        """Incrémente le compteur de tentatives incorrectes"""
        self.tentatives_connexion_incorrectes += 1
        self.derniere_tentative_incorrecte = timezone.now()
        
        # Bloquer automatiquement après 3 tentatives
        if self.tentatives_connexion_incorrectes >= 3:
            self.bloquer("Trop de tentatives de connexion incorrectes")
        else:
            self.save()


class AlerteSecurite(models.Model):
    """Modèle pour les alertes de sécurité"""
    class TypeAlerte(models.TextChoices):
        TENTATIVE_ROLE_INCORRECT = 'TENTATIVE_ROLE_INCORRECT', 'Tentative de connexion avec un rôle incorrect'
        BLOQUAGE_UTILISATEUR = 'BLOQUAGE_UTILISATEUR', 'Utilisateur bloqué'
        DEBLOQUAGE_UTILISATEUR = 'DEBLOQUAGE_UTILISATEUR', 'Utilisateur débloqué'
        CREATION_UTILISATEUR = 'CREATION_UTILISATEUR', 'Création d\'utilisateur par l\'administrateur'
        TENTATIVE_ACCES_NON_AUTORISE = 'TENTATIVE_ACCES_NON_AUTORISE', 'Tentative d\'accès non autorisé'
        VIOLATION_SECURITE = 'VIOLATION_SECURITE', 'Violation de sécurité'
    
    class NiveauUrgence(models.TextChoices):
        BASSE = 'BASSE', 'Basse'
        MOYENNE = 'MOYENNE', 'Moyenne'
        HAUTE = 'HAUTE', 'Haute'
        CRITIQUE = 'CRITIQUE', 'Critique'
    
    type_alerte = models.CharField(max_length=50, choices=TypeAlerte.choices)
    utilisateur_concerne = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='alertes')
    details = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    est_lue = models.BooleanField(default=False)
    niveau_urgence = models.CharField(max_length=20, choices=NiveauUrgence.choices, default=NiveauUrgence.MOYENNE)
    admin_qui_a_bloque = models.ForeignKey(
        Utilisateur, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='alertes_crees'
    )
    adresse_ip = models.CharField(max_length=45, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Alerte de sécurité"
        verbose_name_plural = "Alertes de sécurité"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.type_alerte} - {self.utilisateur_concerne.email} - {self.date_creation}"


class HistoriqueAuthentification(models.Model):
    class TypeAuth(models.TextChoices):
        NFC_CARTE = 'NFC_CARTE', 'Authentification par carte NFC'
        EMPREINTE_NFC = 'EMPREINTE_NFC', 'Authentification par empreinte NFC'
        TENTATIVE_ROLE_INCORRECT = 'TENTATIVE_ROLE_INCORRECT', 'Tentative de connexion avec rôle incorrect'
        AUTRE = 'AUTRE', 'Autre méthode'

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    type_auth = models.CharField(max_length=30, choices=TypeAuth.choices)
    date_heure_acces = models.DateTimeField(auto_now_add=True)
    succes = models.BooleanField()
    adresse_ip = models.CharField(max_length=45)
    user_agent = models.TextField()
    role_tente = models.CharField(max_length=20, blank=True, help_text="Rôle tenté lors de la connexion")
    role_autorise = models.CharField(max_length=20, blank=True, help_text="Rôle autorisé pour cet utilisateur")

    class Meta:
        verbose_name = "Historique d'authentification"
        verbose_name_plural = "Historiques d'authentification"
        ordering = ['-date_heure_acces']

    def __str__(self):
        return f"Auth {self.utilisateur.email} - {self.type_auth} - {'Succès' if self.succes else 'Échec'}"


class HistoriqueJournalisation(models.Model):
    class TypeEvenement(models.TextChoices):
        CREATION = 'CREATION', 'Création'
        MODIFICATION = 'MODIFICATION', 'Modification'
        CONSULTATION = 'CONSULTATION', 'Consultation'
        SUPPRESSION = 'SUPPRESSION', 'Suppression'
        SECURITE = 'SECURITE', 'Événement de sécurité'

    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    date_heure = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=255)
    details = models.TextField()
    type_evenement = models.CharField(max_length=20, choices=TypeEvenement.choices)

    class Meta:
        verbose_name = "Entrée de journal"
        verbose_name_plural = "Journal des événements"
        ordering = ['-date_heure']

    def __str__(self):
        return f"{self.type_evenement} - {self.action}"


class LicenceAcceptation(models.Model):
    """Modèle pour tracer l'acceptation des licences et politiques"""
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE, related_name='licences_acceptees')
    type_licence = models.CharField(
        max_length=50,
        choices=[
            ('POLITIQUE_CONFIDENTIALITE', 'Politique de confidentialité'),
            ('CONDITIONS_UTILISATION', 'Conditions d\'utilisation'),
            ('LICENCE_MEDICALE', 'Licence médicale'),
        ]
    )
    version = models.CharField(max_length=20, default='1.0')
    date_acceptation = models.DateTimeField(auto_now_add=True)
    ip_adresse = models.CharField(max_length=45, blank=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Acceptation de licence"
        verbose_name_plural = "Acceptations de licences"
        unique_together = ['utilisateur', 'type_licence', 'version']
        ordering = ['-date_acceptation']
    
    def __str__(self):
        return f"{self.utilisateur.email} - {self.type_licence} v{self.version}"
class Medecin(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True)
    specialite = models.CharField(max_length=100)
    numero_praticien = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"

    def __str__(self):
        return f"Dr. {self.utilisateur.nom} ({self.specialite})"


class Patient(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True)
    date_naissance = models.DateField()
    numero_dossier = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return f"{self.utilisateur.prenom} {self.utilisateur.nom} (Dossier: {self.numero_dossier})"


class Administrateur(models.Model):
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, primary_key=True)
    niveau_acces = models.IntegerField(default=1)

    class Meta:
        verbose_name = "Administrateur"
        verbose_name_plural = "Administrateurs"

    def __str__(self):
        return f"Admin {self.utilisateur.email} (Niveau {self.niveau_acces})"


class RendezVous(models.Model):
    class StatutRendezVous(models.TextChoices):
        EN_ATTENTE = 'EN_ATTENTE', 'En attente'
        CONFIRME = 'CONFIRME', 'Confirmé'
        ANNULE = 'ANNULE', 'Annulé'

    medecin = models.ForeignKey(Medecin, on_delete=models.CASCADE)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date_heure = models.DateTimeField()
    statut = models.CharField(max_length=20, choices=StatutRendezVous.choices, default=StatutRendezVous.EN_ATTENTE)

    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['date_heure']
        constraints = [
            models.UniqueConstraint(fields=['medecin', 'date_heure'], name='unique_medecin_time'),
            models.UniqueConstraint(fields=['patient', 'date_heure'], name='unique_patient_time')
        ]

    def __str__(self):
        return f"RDV {self.patient} avec {self.medecin} le {self.date_heure}"


class DossierMedical(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    medecin_referent = models.ForeignKey(Medecin, on_delete=models.SET_NULL, null=True, blank=True)
    date_creation = models.DateField(auto_now_add=True)
    resume = models.TextField()
    path_fichier = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Dossier médical"
        verbose_name_plural = "Dossiers médicaux"
        ordering = ['-date_creation']

    def __str__(self):
        return f"Dossier de {self.patient} (Créé le {self.date_creation})"


class EncryptionManager:
    """Gestionnaire de chiffrement pour les données sensibles"""
    
    @staticmethod
    def get_encryption_key():
        """Récupère ou génère la clé de chiffrement"""
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            # Générer une nouvelle clé si elle n'existe pas
            key = Fernet.generate_key()
            # En production, stocker cette clé de manière sécurisée
        return key
    
    @staticmethod
    def encrypt_data(data):
        """Chiffre les données sensibles"""
        if not data:
            return data
        try:
            key = EncryptionManager.get_encryption_key()
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            # En cas d'erreur, retourner les données non chiffrées
            return data
    
    @staticmethod
    def decrypt_data(encrypted_data):
        """Déchiffre les données sensibles"""
        if not encrypted_data:
            return encrypted_data
        try:
            key = EncryptionManager.get_encryption_key()
            f = Fernet(key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            # En cas d'erreur, retourner les données telles quelles
            return encrypted_data


class EncryptedTextField(models.TextField):
    """Champ de texte chiffré automatiquement"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def get_prep_value(self, value):
        """Chiffre la valeur avant sauvegarde"""
        if value:
            return EncryptionManager.encrypt_data(value)
        return value
    
    def from_db_value(self, value, expression, connection):
        """Déchiffre la valeur depuis la base de données"""
        if value:
            return EncryptionManager.decrypt_data(value)
        return value
    
    def to_python(self, value):
        """Conversion Python"""
        if isinstance(value, str):
            return value
        return str(value) if value is not None else None


class AuditLog(models.Model):
    """Modèle pour l'audit complet des accès et actions"""
    class TypeAction(models.TextChoices):
        CONNEXION = 'CONNEXION', 'Connexion'
        DECONNEXION = 'DECONNEXION', 'Déconnexion'
        LECTURE_DONNEES = 'LECTURE_DONNEES', 'Lecture de données'
        MODIFICATION_DONNEES = 'MODIFICATION_DONNEES', 'Modification de données'
        SUPPRESSION_DONNEES = 'SUPPRESSION_DONNEES', 'Suppression de données'
        ACCES_MEDICAL = 'ACCES_MEDICAL', 'Accès aux données médicales'
        ACCES_PATIENT = 'ACCES_PATIENT', 'Accès aux données patient'
        BLOQUAGE_UTILISATEUR = 'BLOQUAGE_UTILISATEUR', 'Blocage d\'utilisateur'
        DEBLOQUAGE_UTILISATEUR = 'DEBLOQUAGE_UTILISATEUR', 'Déblocage d\'utilisateur'
        VIOLATION_SECURITE = 'VIOLATION_SECURITE', 'Violation de sécurité'
    
    class NiveauRisque(models.TextChoices):
        FAIBLE = 'FAIBLE', 'Faible'
        MOYEN = 'MOYEN', 'Moyen'
        ELEVE = 'ELEVE', 'Élevé'
        CRITIQUE = 'CRITIQUE', 'Critique'
    
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    type_action = models.CharField(max_length=50, choices=TypeAction.choices)
    description = models.TextField()
    date_heure = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.CharField(max_length=45)
    user_agent = models.TextField()
    url_accedee = models.CharField(max_length=500, blank=True)
    donnees_consultees = models.TextField(blank=True, help_text="Données consultées (chiffrées)")
    niveau_risque = models.CharField(max_length=20, choices=NiveauRisque.choices, default=NiveauRisque.MOYEN)
    session_id = models.CharField(max_length=100, blank=True)
    est_suspect = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Log d'audit"
        verbose_name_plural = "Logs d'audit"
        ordering = ['-date_heure']
        indexes = [
            models.Index(fields=['utilisateur', 'date_heure']),
            models.Index(fields=['type_action', 'date_heure']),
            models.Index(fields=['niveau_risque', 'date_heure']),
        ]
    
    def __str__(self):
        return f"{self.type_action} - {self.utilisateur.email if self.utilisateur else 'Anonyme'} - {self.date_heure}"
    
    @classmethod
    def log_action(cls, utilisateur, type_action, description, request, niveau_risque=NiveauRisque.MOYEN, donnees_consultees=None):
        """Méthode utilitaire pour logger une action"""
        try:
            # Chiffrer les données sensibles si nécessaire
            donnees_chiffrees = ''
            if donnees_consultees:
                donnees_chiffrees = EncryptionManager.encrypt_data(str(donnees_consultees))
            
            cls.objects.create(
                utilisateur=utilisateur,
                type_action=type_action,
                description=description,
                adresse_ip=request.META.get('REMOTE_ADDR', ''),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                url_accedee=request.path,
                donnees_consultees=donnees_chiffrees,
                niveau_risque=niveau_risque,
                session_id=request.session.session_key if request.session else '',
            )
        except Exception as e:
            # En cas d'erreur, logger quand même
            logger.error(f"Erreur lors du logging d'audit: {e}")
    
    @classmethod
    def detecter_anomalies(cls, heures=24):
        """Détecte les anomalies dans les logs d'audit"""
        from django.utils import timezone
        from datetime import timedelta
        
        date_limite = timezone.now() - timedelta(hours=heures)
        
        # Actions suspectes
        actions_suspectes = cls.objects.filter(
            date_heure__gte=date_limite,
            niveau_risque__in=[cls.NiveauRisque.ELEVE, cls.NiveauRisque.CRITIQUE]
        )
        
        # Accès multiples depuis différentes IP
        acces_multiples = cls.objects.filter(
            date_heure__gte=date_limite,
            type_action=cls.TypeAction.CONNEXION
        ).values('utilisateur', 'adresse_ip').annotate(
            count=models.Count('id')
        ).filter(count__gt=5)
        
        return {
            'actions_suspectes': actions_suspectes,
            'acces_multiples': acces_multiples,
        }


