#!/bin/bash
set -e

echo "🚀 Démarrage de KeurDoctor (Version Locale) avec Keycloak..."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les messages colorés
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier si Python et l'environnement virtuel existent
if [ -d "../KDenv" ]; then
    print_status "Environnement virtuel Python détecté."
    USE_LOCAL_DJANGO=true
else
    print_warning "Pas d'environnement virtuel détecté. Utilisation de Docker pour Django."
    USE_LOCAL_DJANGO=false
fi

print_info "Mode de démarrage: ${USE_LOCAL_DJANGO}"

# Nettoyer les conteneurs existants
print_status "Nettoyage des conteneurs existants..."
docker-compose down --remove-orphans 2>/dev/null || true

if [ "$USE_LOCAL_DJANGO" = true ]; then
    print_status "🐍 Démarrage en mode local Python..."
    
    # Démarrer seulement Keycloak et PostgreSQL via Docker
    print_status "Démarrage de Keycloak et PostgreSQL via Docker..."
    docker-compose up -d keycloak_dev postgres
    
    # Attendre que les services Docker soient prêts
    print_status "Attente du démarrage de Keycloak..."
    sleep 15
    
    # Activer l'environnement virtuel et démarrer Django
    print_status "Activation de l'environnement virtuel et démarrage de Django..."
    
    # Vérifier si l'environnement virtuel existe
    if [ -f "../KDenv/bin/activate" ]; then
        source ../KDenv/bin/activate
        
        # Installer les dépendances si nécessaire
        print_status "Installation des dépendances Python..."
        pip install -r requirements.txt
        
        # Effectuer les migrations
        print_status "Exécution des migrations Django..."
        python manage.py migrate
        
        # Démarrer Django en arrière-plan
        print_status "Démarrage du serveur Django..."
        python manage.py runserver 0.0.0.0:8000 &
        DJANGO_PID=$!
        
        # Sauvegarder le PID pour pouvoir arrêter Django plus tard
        echo $DJANGO_PID > .django_pid
        
        print_status "Django démarré avec PID: $DJANGO_PID"
    else
        print_error "Environnement virtuel non trouvé dans ../KDenv/"
        exit 1
    fi
    
else
    # Construire et démarrer tous les services via Docker
    print_status "🐳 Démarrage en mode Docker complet..."
    print_status "Construction et démarrage des services..."
    
    # Essayer de construire sans cache en cas de problème de réseau
    docker-compose build --no-cache --build-arg PIP_TIMEOUT=300 || {
        print_warning "Échec de la construction. Tentative sans cache..."
        docker-compose build --no-cache --pull
    }
    
    docker-compose up -d
    
    # Attendre que les services soient prêts
    print_status "Attente du démarrage des services..."
    sleep 15
fi

# Vérifier l'état des services
print_status "Vérification de l'état des services..."

# Keycloak
print_status "Vérification de Keycloak..."
for i in {1..30}; do
    if curl -f http://localhost:8080/health/live >/dev/null 2>&1; then
        print_status "✅ Keycloak est opérationnel sur http://localhost:8080"
        break
    elif [ $i -eq 30 ]; then
        print_warning "⚠️  Keycloak n'est pas encore prêt après 30 tentatives"
    else
        echo -n "."
        sleep 2
    fi
done

# Django
print_status "Vérification de Django..."
for i in {1..15}; do
    if curl -f http://localhost:8000 >/dev/null 2>&1; then
        print_status "✅ Django est opérationnel sur http://localhost:8000"
        break
    elif [ $i -eq 15 ]; then
        print_warning "⚠️  Django n'est pas encore prêt"
    else
        echo -n "."
        sleep 2
    fi
done

echo ""
print_status "📋 Instructions de configuration:"
echo "1. Accédez à Keycloak Admin: http://localhost:8080/admin"
echo "   - Utilisateur: admin"
echo "   - Mot de passe: admin"
echo ""
echo "2. Créez un realm 'KeurDoctorSecure'"
echo "3. Créez un client 'django-KDclient'"
echo "4. Configurez les rôles: admin, medecin, patient"
echo "5. Accédez à votre application: http://localhost:8000"
echo ""
print_status "🔧 Commandes utiles:"
if [ "$USE_LOCAL_DJANGO" = true ]; then
    echo "- Arrêter Django: ./stop.sh"
    echo "- Voir les logs Django: tail -f django.log"
    echo "- Voir les logs Keycloak: docker-compose logs keycloak_dev"
else
    echo "- Voir les logs: docker-compose logs -f"
    echo "- Arrêter: docker-compose down"
    echo "- Redémarrer: docker-compose restart"
fi
echo ""
print_status "Démarrage terminé! 🎉"

if [ "$USE_LOCAL_DJANGO" = true ]; then
    print_info "Django fonctionne en mode local. Utilisez './stop.sh' pour arrêter proprement."
fi
