#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.contrib import admin
from comptes.models import *

print("Test de l'enregistrement admin complet :")
print("========================================")

# Vérifier les modèles enregistrés dans l'admin
registered_models = admin.site._registry.keys()
print(f"\nModèles enregistrés dans l'admin ({len(registered_models)}) :")

for model in registered_models:
    model_name = model._meta.verbose_name if hasattr(model._meta, 'verbose_name') else model.__name__
    table_name = model._meta.db_table if hasattr(model._meta, 'db_table') else 'N/A'
    print(f"  ✅ {model_name} ({model.__name__}) -> table: {table_name}")

# Vérifier spécifiquement les modèles clés
models_to_check = [
    ('Utilisateur', Utilisateur),
    ('MedecinNew', MedecinNew), 
    ('PatientNew', PatientNew),
    ('SpecialiteMedicale', SpecialiteMedicale),
    ('Consultation', Consultation),
    ('RendezVous', RendezVous)
]

print(f"\n🔍 Vérification des modèles clés :")
for nom, model in models_to_check:
    if model in registered_models:
        print(f"  ✅ {nom} - OK")
    else:
        print(f"  ❌ {nom} - MANQUANT")

print(f"\n🎯 Résolution du problème 404 :")
if Utilisateur in registered_models:
    print(f"  ✅ Modèle Utilisateur maintenant enregistré")
    print(f"  ✅ L'URL http://localhost:8000/admin/comptes/utilisateur/226/change/ devrait fonctionner")
else:
    print(f"  ❌ Problème persistant avec le modèle Utilisateur")
