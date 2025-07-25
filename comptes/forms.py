from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Medecin, Patient, RFIDCard

class InscriptionForm(UserCreationForm):
    ROLE_CHOICES = [
        ('medecin', 'Médecin'),
        ('patient', 'Patient'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Rôle',
        widget=forms.RadioSelect,
        required=True
    )
    
    # Champs spécifiques au médecin
    specialite = forms.CharField(
        max_length=100,
        required=False,
        label='Spécialité',
        help_text='Champ obligatoire pour les médecins'
    )
    numero_praticien = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de praticien',
        help_text='Champ obligatoire pour les médecins'
    )
    
    # Champs spécifiques au patient
    date_naissance = forms.DateField(
        required=False,
        label='Date de naissance',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Champ obligatoire pour les patients'
    )
    numero_dossier = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de dossier',
        help_text='Champ optionnel pour les patients. Laissez vide pour génération automatique.'
    )
    
    # Nouveaux champs RFID
    rfid_uid = forms.CharField(
        max_length=64,
        required=False,
        label='UID Carte RFID',
        help_text='Scannez la carte RFID pour l\'identification'
    )
    badge_bleu_uid = forms.CharField(
        max_length=64,
        required=False,
        label='UID Badge Bleu',
        help_text='Scannez le badge bleu pour le contrôle de session'
    )
    
    class Meta:
        model = Utilisateur
        fields = ('email', 'prenom', 'nom', 'password1', 'password2', 'role')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre les champs de mot de passe optionnels (géré par Keycloak)
        self.fields['password1'].required = False
        self.fields['password2'].required = False
        self.fields['password1'].widget.attrs.update({'style': 'display: none;'})
        self.fields['password2'].widget.attrs.update({'style': 'display: none;'})
    
    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        
        if role == 'medecin':
            if not cleaned_data.get('specialite'):
                raise forms.ValidationError("La spécialité est obligatoire pour les médecins.")
            if not cleaned_data.get('numero_praticien'):
                raise forms.ValidationError("Le numéro de praticien est obligatoire pour les médecins.")
        elif role == 'patient':
            if not cleaned_data.get('date_naissance'):
                raise forms.ValidationError("La date de naissance est obligatoire pour les patients.")
            # Le numéro de dossier est maintenant optionnel
        
        return cleaned_data


class AdminCreateUserForm(UserCreationForm):
    """Formulaire pour la création d'utilisateurs par l'administrateur"""
    ROLE_CHOICES = [
        ('admin', 'Administrateur'),
        ('medecin', 'Médecin'),
        ('patient', 'Patient'),
    ]
    
    role_autorise = forms.ChoiceField(
        choices=ROLE_CHOICES,
        label='Rôle autorisé',
        required=True
    )
    
    # Champs spécifiques au médecin
    specialite = forms.CharField(
        max_length=100,
        required=False,
        label='Spécialité',
        help_text='Champ obligatoire pour les médecins'
    )
    numero_praticien = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de praticien',
        help_text='Champ obligatoire pour les médecins'
    )
    
    # Champs spécifiques au patient
    date_naissance = forms.DateField(
        required=False,
        label='Date de naissance',
        widget=forms.DateInput(attrs={'type': 'date'}),
        help_text='Champ obligatoire pour les patients'
    )
    numero_dossier = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de dossier',
        help_text='Champ optionnel pour les patients. Laissez vide pour génération automatique.'
    )
    
    # Champs spécifiques à l'admin
    niveau_acces = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        required=False,
        label='Niveau d\'accès',
        help_text='Niveau d\'accès pour les administrateurs'
    )
    
    # Champs RFID
    rfid_uid = forms.CharField(
        max_length=64,
        required=False,
        label='UID Carte RFID',
        help_text='Scannez la carte RFID pour l\'identification'
    )
    badge_bleu_uid = forms.CharField(
        max_length=64,
        required=False,
        label='UID Badge Bleu',
        help_text='Scannez le badge bleu pour le contrôle de session'
    )
    
    class Meta:
        model = Utilisateur
        fields = ('email', 'prenom', 'nom', 'password1', 'password2', 'role_autorise')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personnaliser les widgets
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['prenom'].widget.attrs.update({'class': 'form-control'})
        self.fields['nom'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Ajouter des placeholders
        self.fields['email'].widget.attrs.update({'placeholder': 'exemple@email.com'})
        self.fields['prenom'].widget.attrs.update({'placeholder': 'Prénom'})
        self.fields['nom'].widget.attrs.update({'placeholder': 'Nom'})
    
    def clean(self):
        cleaned_data = super().clean()
        role_autorise = cleaned_data.get('role_autorise')
        
        # Validation selon le rôle
        if role_autorise == 'medecin':
            if not cleaned_data.get('specialite'):
                raise forms.ValidationError("La spécialité est obligatoire pour les médecins.")
            if not cleaned_data.get('numero_praticien'):
                raise forms.ValidationError("Le numéro de praticien est obligatoire pour les médecins.")
        elif role_autorise == 'patient':
            if not cleaned_data.get('date_naissance'):
                raise forms.ValidationError("La date de naissance est obligatoire pour les patients.")
        
        return cleaned_data


class RFIDCardRegisterForm(forms.ModelForm):
    utilisateur = forms.ModelChoiceField(queryset=Utilisateur.objects.filter(role_autorise__in=['admin', 'patient']), required=False, label="Utilisateur (pour les admins)")
    card_uid = forms.CharField(max_length=64, label="UID de la carte RFID")

    class Meta:
        model = RFIDCard
        fields = ['utilisateur', 'card_uid']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if not user or user.role_autorise != 'admin':
            self.fields.pop('utilisateur') 