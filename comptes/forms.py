from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Utilisateur, Medecin, Patient

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
<<<<<<< HEAD
        help_text='Champ optionnel pour les patients. Laissez vide pour génération automatique.'
=======
        help_text='Champ obligatoire pour les patients'
>>>>>>> ce737485fc5282521a7973d893496f32ae35fa49
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
<<<<<<< HEAD
            # Le numéro de dossier est maintenant optionnel
=======
            if not cleaned_data.get('numero_dossier'):
                raise forms.ValidationError("Le numéro de dossier est obligatoire pour les patients.")
        
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
        label='Rôle à attribuer',
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
        help_text='Sélectionnez le rôle à attribuer à cet utilisateur'
    )
    
    # Champs spécifiques au médecin
    specialite = forms.CharField(
        max_length=100,
        required=False,
        label='Spécialité',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Champ obligatoire pour les médecins'
    )
    numero_praticien = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de praticien',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Champ obligatoire pour les médecins'
    )
    
    # Champs spécifiques au patient
    date_naissance = forms.DateField(
        required=False,
        label='Date de naissance',
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        help_text='Champ obligatoire pour les patients'
    )
    numero_dossier = forms.CharField(
        max_length=50,
        required=False,
        label='Numéro de dossier',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        help_text='Champ obligatoire pour les patients'
    )
    
    # Champs spécifiques à l'administrateur
    niveau_acces = forms.IntegerField(
        required=False,
        label='Niveau d\'accès',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '10'}),
        help_text='Niveau d\'accès pour les administrateurs (1-10)',
        initial=1
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
        
        if role_autorise == 'medecin':
            if not cleaned_data.get('specialite'):
                raise forms.ValidationError("La spécialité est obligatoire pour les médecins.")
            if not cleaned_data.get('numero_praticien'):
                raise forms.ValidationError("Le numéro de praticien est obligatoire pour les médecins.")
        elif role_autorise == 'patient':
            if not cleaned_data.get('date_naissance'):
                raise forms.ValidationError("La date de naissance est obligatoire pour les patients.")
            if not cleaned_data.get('numero_dossier'):
                raise forms.ValidationError("Le numéro de dossier est obligatoire pour les patients.")
        elif role_autorise == 'admin':
            if not cleaned_data.get('niveau_acces'):
                raise forms.ValidationError("Le niveau d'accès est obligatoire pour les administrateurs.")
>>>>>>> ce737485fc5282521a7973d893496f32ae35fa49
        
        return cleaned_data 