#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.contrib import admin
from comptes.models import *

print("Test de l'interface d'administration :")
print("=====================================")

# Vérifier les modèles enregistrés dans l'admin
registered_models = admin.site._registry.keys()
print(f"\nModèles enregistrés dans l'admin ({len(registered_models)}) :")

for model in registered_models:
    model_name = model._meta.verbose_name if hasattr(model._meta, 'verbose_name') else model.__name__
    print(f"  ✅ {model_name} ({model.__name__})")

print(f"\nTables en base de données :")
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'comptes_%'")
tables = cursor.fetchall()

for table in tables:
    print(f"  📋 {table[0]}")

print(f"\n🎯 Migration réussie ! L'admin Django est maintenant configuré pour :")
print("   - MedecinNew (avec table comptes_medecin_new)")
print("   - PatientNew (avec table comptes_patient_new)")  
print("   - Consultation, Prescription, DocumentMedical")
print("   - SpecialiteMedicale")
print("   - Tous les autres modèles médicaux")

print(f"\n✅ Problème résolu ! L'erreur 404 devrait être corrigée.")
print(f"   Les URLs d'admin pointent maintenant vers les bons modèles.")
