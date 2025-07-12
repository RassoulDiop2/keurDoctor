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
        help_text='Champ optionnel pour les patients. Laissez vide pour génération automatique.'
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