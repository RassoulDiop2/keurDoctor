FROM python:3.11-slim

# Arguments de build
ARG PIP_TIMEOUT=120

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Mise à jour de pip et configuration des timeouts
RUN pip install --upgrade pip

# Copie et installation des dépendances Python avec timeout étendu
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=${PIP_TIMEOUT} --retries=5 -r requirements.txt

# Copie du code source
COPY . .

# Variables d'environnement
ENV PYTHONPATH=/app
ENV DJANGO_SETTINGS_MODULE=keur_Doctor_app.settings

# Port d'exposition
EXPOSE 8000

# Script de démarrage
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
