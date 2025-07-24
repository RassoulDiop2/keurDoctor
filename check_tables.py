#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'keur_Doctor_app.settings')
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name LIKE 'comptes_%'")
tables = cursor.fetchall()

print("Tables dans la base de données :")
print("=================================")
for table in tables:
    print(f"- {table[0]}")

print(f"\nTotal: {len(tables)} tables")
