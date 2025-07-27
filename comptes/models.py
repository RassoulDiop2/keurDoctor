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

# --- Début du déplacement ---
class EncryptionManager:
    """Gestionnaire de chiffrement pour les données sensibles"""
    @staticmethod
    def get_encryption_key():
        key = getattr(settings, 'ENCRYPTION_KEY', None)
        if not key:
            key = Fernet.generate_key()
        return key
    @staticmethod
    def encrypt_data(data):
        if not data:
            return data
        try:
            key = EncryptionManager.get_encryption_key()
            f = Fernet(key)
            encrypted_data = f.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            return data
    @staticmethod
    def decrypt_data(encrypted_data):
        if not encrypted_data:
            return encrypted_data
        try:
            key = EncryptionManager.get_encryption_key()
            f = Fernet(key)
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = f.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            return encrypted_data

class EncryptedTextField(models.TextField):
    """Champ de texte chiffré automatiquement"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    def get_prep_value(self, value):
        if value:
            return EncryptionManager.encrypt_data(value)
        return value
    def from_db_value(self, value, expression, connection):
        if value:
            return EncryptionManager.decrypt_data(value)
        return value
    def to_python(self, value):
        if isinstance(value, str):
            return value
        return str(value) if value is not None else None
# --- Fin du déplacement ---

# Modèles métier supprimés - versions complètes en fin de fichier


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
    session_id = models.CharField(max_length=100, blank=True, null=True)
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
            
            # ✅ CORRECTION: Vérifier si l'utilisateur est authentifié
            user_to_log = None
            if utilisateur and hasattr(utilisateur, 'is_authenticated') and utilisateur.is_authenticated:
                # S'assurer que c'est une instance d'Utilisateur et non AnonymousUser
                if hasattr(utilisateur, 'email') and not utilisateur.__class__.__name__ == 'AnonymousUser':
                    user_to_log = utilisateur
            
            cls.objects.create(
                utilisateur=user_to_log,  # ✅ Sera None pour les utilisateurs anonymes
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
            # En cas d'erreur, logger quand même mais avec plus de détails
            logger.error(f"Erreur lors du logging d'audit: {e} - Utilisateur: {type(utilisateur).__name__}")
    
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


class RFIDCard(models.Model):
    """Carte RFID liée à un utilisateur pour l'authentification forte."""
    utilisateur = models.ForeignKey('Utilisateur', on_delete=models.CASCADE, related_name='rfid_cards')
    card_uid = models.CharField(max_length=64, unique=True, help_text="Identifiant unique de la carte RFID")
    date_enregistrement = models.DateTimeField(auto_now_add=True)
    actif = models.BooleanField(default=True)
    access_direct = models.BooleanField(default=False, help_text="Permet l'accès direct au dashboard sans OTP")

    class Meta:
        verbose_name = "Carte RFID utilisateur"
        verbose_name_plural = "Cartes RFID utilisateurs"
        ordering = ['-date_enregistrement']

    def __str__(self):
        return f"{self.card_uid} ({self.utilisateur.email}) - {'Accès direct' if self.access_direct else 'Avec OTP'}"


# ===== NOUVEAUX MODÈLES POUR LES FONCTIONNALITÉS MÉDICALES =====

class SpecialiteMedicale(models.Model):
    """Spécialités médicales disponibles"""
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        verbose_name = "Spécialité médicale"
        verbose_name_plural = "Spécialités médicales"
        ordering = ['nom']
    
    def __str__(self):
        return self.nom


class MedecinNew(models.Model):
    """Profil étendu pour les médecins"""
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='profil_medecin_new')
    numero_ordre = models.CharField(max_length=20, unique=True, help_text="Numéro d'ordre du conseil médical", default="NON_RENSEIGNE")
    specialites = models.ManyToManyField(SpecialiteMedicale, blank=True)
    telephone_cabinet = models.CharField(max_length=20, blank=True)
    adresse_cabinet = models.TextField(blank=True)
    horaires_consultation = models.TextField(blank=True, help_text="Horaires de consultation")
    tarif_consultation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accepte_nouveaux_patients = models.BooleanField(default=True)
    date_installation = models.DateField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Médecin"
        verbose_name_plural = "Médecins"
        db_table = 'comptes_medecin_new'
    
    def __str__(self):
        return f"Dr. {self.utilisateur.prenom} {self.utilisateur.nom}"
    
    @property
    def patients_actifs(self):
        return Patient.objects.filter(medecin_traitant=self).count()
    
    @property
    def rdv_cette_semaine(self):
        from datetime import date, timedelta
        debut_semaine = date.today() - timedelta(days=date.today().weekday())
        fin_semaine = debut_semaine + timedelta(days=6)
        return RendezVous.objects.filter(
            medecin=self,
            date_rdv__range=[debut_semaine, fin_semaine],
            statut__in=['confirme', 'en_attente']
        ).count()


class PatientNew(models.Model):
    """Profil étendu pour les patients"""
    utilisateur = models.OneToOneField(Utilisateur, on_delete=models.CASCADE, related_name='profil_patient_new')
    numero_securite_sociale = models.CharField(max_length=15, unique=True, blank=True)
    date_naissance = models.DateField()
    telephone = models.CharField(max_length=20, blank=True)
    adresse = models.TextField(blank=True)
    medecin_traitant = models.ForeignKey('MedecinNew', on_delete=models.SET_NULL, null=True, blank=True, related_name='patients')
    groupe_sanguin = models.CharField(max_length=5, blank=True)
    allergies_connues = models.TextField(blank=True)
    antecedents_medicaux = models.TextField(blank=True)
    personne_a_contacter_nom = models.CharField(max_length=100, blank=True)
    personne_a_contacter_telephone = models.CharField(max_length=20, blank=True)
    
    class Meta:
        verbose_name = "Patient"
        verbose_name_plural = "Patients"
        db_table = 'comptes_patient_new'
    
    def __str__(self):
        return f"{self.utilisateur.prenom} {self.utilisateur.nom}"
    
    @property
    def age(self):
        from datetime import date
        today = date.today()
        return today.year - self.date_naissance.year - ((today.month, today.day) < (self.date_naissance.month, self.date_naissance.day))
    
    @property
    def derniere_consultation(self):
        return Consultation.objects.filter(patient=self).order_by('-date_consultation').first()


class RendezVous(models.Model):
    """Gestion des rendez-vous"""
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('confirme', 'Confirmé'),
        ('annule', 'Annulé'),
        ('termine', 'Terminé'),
        ('absent', 'Patient absent'),
    ]
    
    TYPE_CHOICES = [
        ('consultation', 'Consultation'),
        ('visite_controle', 'Visite de contrôle'),
        ('urgence', 'Urgence'),
        ('teleconsultation', 'Téléconsultation'),
    ]
    
    patient = models.ForeignKey('PatientNew', on_delete=models.CASCADE, related_name='rendez_vous')
    medecin = models.ForeignKey('MedecinNew', on_delete=models.CASCADE, related_name='rendez_vous')
    date_rdv = models.DateTimeField()
    duree_prevue = models.IntegerField(default=30, help_text="Durée en minutes")
    type_rdv = models.CharField(max_length=20, choices=TYPE_CHOICES, default='consultation')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    motif = models.TextField()
    notes_secretariat = models.TextField(blank=True)
    date_creation = models.DateTimeField(default=timezone.now)
    date_modification = models.DateTimeField(default=timezone.now)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        verbose_name = "Rendez-vous"
        verbose_name_plural = "Rendez-vous"
        ordering = ['date_rdv']
    
    def __str__(self):
        return f"{self.patient} - {self.medecin} - {self.date_rdv.strftime('%d/%m/%Y %H:%M')}"


class Consultation(models.Model):
    """Consultations médicales et dossiers"""
    rendez_vous = models.OneToOneField(RendezVous, on_delete=models.CASCADE, null=True, blank=True)
    patient = models.ForeignKey('PatientNew', on_delete=models.CASCADE, related_name='consultations')
    medecin = models.ForeignKey('MedecinNew', on_delete=models.CASCADE, related_name='consultations')
    date_consultation = models.DateTimeField()
    motif_consultation = models.TextField()
    symptomes = models.TextField(blank=True)
    examen_clinique = models.TextField(blank=True)
    diagnostic = models.TextField(blank=True)
    traitement_prescrit = models.TextField(blank=True)
    examens_complements = models.TextField(blank=True, help_text="Examens complémentaires prescrits")
    observations = models.TextField(blank=True)
    prochaine_visite = models.DateField(null=True, blank=True)
    confidentialite = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Consultation"
        verbose_name_plural = "Consultations"
        ordering = ['-date_consultation']
    
    def __str__(self):
        return f"Consultation {self.patient} - {self.date_consultation.strftime('%d/%m/%Y')}"


class Prescription(models.Model):
    """Ordonnances et prescriptions"""
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='prescriptions')
    medicament = models.CharField(max_length=200)
    posologie = models.TextField()
    duree_traitement = models.CharField(max_length=100)
    instructions_particulieres = models.TextField(blank=True)
    date_prescription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        ordering = ['-date_prescription']
    
    def __str__(self):
        return f"{self.medicament} - {self.consultation.patient}"


# Alias temporaires pour la compatibilité 
Medecin = MedecinNew
Patient = PatientNew

class DossierMedical(models.Model):
    """Dossier médical complet du patient"""
    patient = models.OneToOneField('PatientNew', on_delete=models.CASCADE, related_name='dossier_medical')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_mise_a_jour = models.DateTimeField(auto_now=True)
    notes_importantes = models.TextField(blank=True)
    statut = models.CharField(max_length=20, choices=[
        ('actif', 'Actif'),
        ('archive', 'Archivé'),
        ('transfere', 'Transféré'),
    ], default='actif')
    
    class Meta:
        verbose_name = "Dossier médical"
        verbose_name_plural = "Dossiers médicaux"
    
    def __str__(self):
        return f"Dossier de {self.patient}"
    
    @property
    def derniere_consultation(self):
        return self.patient.consultations.order_by('-date_consultation').first()
    
    @property
    def nombre_consultations(self):
        return self.patient.consultations.count()


class DocumentMedical(models.Model):
    """Documents liés au dossier médical"""
    TYPE_CHOICES = [
        ('ordonnance', 'Ordonnance'),
        ('resultat_examen', 'Résultat d\'examen'),
        ('courrier_medical', 'Courrier médical'),
        ('imagerie', 'Imagerie médicale'),
        ('autres', 'Autres'),
    ]
    
    dossier = models.ForeignKey(DossierMedical, on_delete=models.CASCADE, related_name='documents')
    type_document = models.CharField(max_length=20, choices=TYPE_CHOICES)
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    fichier = models.FileField(upload_to='documents_medicaux/', blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    cree_par = models.ForeignKey(Utilisateur, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        verbose_name = "Document médical"
        verbose_name_plural = "Documents médicaux"
        ordering = ['-date_creation']
    
    def __str__(self):
        return f"{self.titre} - {self.dossier.patient}"


# Signaux Django pour synchronisation automatique des groupes
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Utilisateur)
def sync_user_groups_on_role_change(sender, instance, created, **kwargs):
    """
    Signal qui synchronise automatiquement les groupes Django
    quand le rôle d'un utilisateur est modifié
    """
    if instance.role_autorise:
        try:
            # Import local pour éviter les imports circulaires
            from .views import sync_django_groups
            
            # Synchroniser les groupes Django
            success = sync_django_groups(instance, instance.role_autorise)
            
            if success:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"✅ Groupes Django auto-synchronisés pour {instance.email} (rôle: {instance.role_autorise})")
            
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"❌ Erreur auto-sync groupes Django pour {instance.email}: {e}")

