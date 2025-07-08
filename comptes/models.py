from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager
import uuid
from django.utils import timezone


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

