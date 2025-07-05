#!/bin/bash

# Script de déploiement du thème Keycloak CHIFT
# Usage: ./deploy-theme.sh [dev|prod]

set -e

# Configuration
THEME_NAME="chift-theme"
THEME_DIR="keycloak-themes/$THEME_NAME"
KEYCLOAK_CONTAINER="keycloak"  # Nom du conteneur Docker
KEYCLOAK_THEMES_DIR="/opt/keycloak/themes"

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonctions utilitaires
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier si le thème existe
check_theme_exists() {
    if [ ! -d "$THEME_DIR" ]; then
        log_error "Le dossier du thème $THEME_DIR n'existe pas!"
        exit 1
    fi
    log_success "Thème trouvé dans $THEME_DIR"
}

# Vérifier si Docker est disponible
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé ou n'est pas disponible"
        exit 1
    fi
    log_success "Docker est disponible"
}

# Vérifier si le conteneur Keycloak existe et fonctionne
check_keycloak_container() {
    if ! docker ps | grep -q "$KEYCLOAK_CONTAINER"; then
        log_error "Le conteneur Keycloak '$KEYCLOAK_CONTAINER' n'est pas en cours d'exécution"
        log_info "Démarrage du conteneur..."
        docker-compose up -d keycloak
        sleep 10
    fi
    log_success "Conteneur Keycloak '$KEYCLOAK_CONTAINER' est actif"
}

# Copier le thème dans le conteneur
deploy_theme() {
    log_info "Copie du thème dans le conteneur Keycloak..."
    
    # Créer le dossier themes si nécessaire
    docker exec "$KEYCLOAK_CONTAINER" mkdir -p "$KEYCLOAK_THEMES_DIR" 2>/dev/null || true
    
    # Copier le thème
    docker cp "$THEME_DIR" "$KEYCLOAK_CONTAINER:$KEYCLOAK_THEMES_DIR/"
    
    # Vérifier les permissions
    docker exec "$KEYCLOAK_CONTAINER" chown -R keycloak:keycloak "$KEYCLOAK_THEMES_DIR/$THEME_NAME"
    
    log_success "Thème copié avec succès!"
}

# Configuration pour le développement
configure_dev() {
    log_info "Configuration pour l'environnement de développement..."
    
    # Variables d'environnement pour désactiver le cache
    cat << EOF >> .env.dev
KC_SPI_THEME_STATIC_MAX_AGE=-1
KC_SPI_THEME_CACHE_THEMES=false
KC_SPI_THEME_CACHE_TEMPLATES=false
KC_LOG_LEVEL=INFO
EOF
    
    log_success "Configuration de développement appliquée"
    log_warning "Redémarrez Keycloak pour appliquer les changements de cache"
}

# Configuration pour la production
configure_prod() {
    log_info "Configuration pour l'environnement de production..."
    
    # Variables d'environnement pour activer le cache
    cat << EOF >> .env.prod
KC_SPI_THEME_STATIC_MAX_AGE=31536000
KC_SPI_THEME_CACHE_THEMES=true
KC_SPI_THEME_CACHE_TEMPLATES=true
KC_LOG_LEVEL=WARN
EOF
    
    log_success "Configuration de production appliquée"
}

# Vérifier le déploiement
verify_deployment() {
    log_info "Vérification du déploiement..."
    
    if docker exec "$KEYCLOAK_CONTAINER" test -d "$KEYCLOAK_THEMES_DIR/$THEME_NAME"; then
        log_success "Thème déployé avec succès dans le conteneur"
        
        # Lister les fichiers du thème
        log_info "Contenu du thème déployé:"
        docker exec "$KEYCLOAK_CONTAINER" find "$KEYCLOAK_THEMES_DIR/$THEME_NAME" -type f | head -10
    else
        log_error "Échec du déploiement du thème"
        exit 1
    fi
}

# Redémarrer Keycloak
restart_keycloak() {
    log_info "Redémarrage de Keycloak..."
    docker-compose restart keycloak
    
    # Attendre que Keycloak soit prêt
    log_info "Attente du démarrage de Keycloak..."
    sleep 30
    
    # Vérifier si Keycloak répond
    if docker exec "$KEYCLOAK_CONTAINER" curl -f http://localhost:8080/health/ready 2>/dev/null; then
        log_success "Keycloak est prêt!"
    else
        log_warning "Keycloak met du temps à démarrer, veuillez patienter..."
    fi
}

# Fonction d'aide
show_help() {
    cat << EOF
Usage: $0 [ENVIRONMENT] [OPTIONS]

ENVIRONMENT:
    dev     Déploiement pour développement (cache désactivé)
    prod    Déploiement pour production (cache activé)

OPTIONS:
    --no-restart    Ne pas redémarrer Keycloak après le déploiement
    --verify-only   Vérifier uniquement le déploiement existant
    --help         Afficher cette aide

Exemples:
    $0 dev                    # Déploiement développement avec redémarrage
    $0 prod --no-restart      # Déploiement production sans redémarrage
    $0 --verify-only          # Vérification uniquement

EOF
}

# Variables
ENVIRONMENT=""
NO_RESTART=false
VERIFY_ONLY=false

# Traitement des arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        dev|prod)
            ENVIRONMENT="$1"
            shift
            ;;
        --no-restart)
            NO_RESTART=true
            shift
            ;;
        --verify-only)
            VERIFY_ONLY=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Option inconnue: $1"
            show_help
            exit 1
            ;;
    esac
done

# Script principal
main() {
    log_info "🚀 Démarrage du déploiement du thème Keycloak CHIFT"
    
    # Vérifications préliminaires
    check_docker
    check_theme_exists
    
    if [ "$VERIFY_ONLY" = true ]; then
        check_keycloak_container
        verify_deployment
        exit 0
    fi
    
    check_keycloak_container
    
    # Déploiement
    deploy_theme
    
    # Configuration selon l'environnement
    case $ENVIRONMENT in
        dev)
            configure_dev
            ;;
        prod)
            configure_prod
            ;;
        "")
            log_warning "Aucun environnement spécifié, utilisation des paramètres par défaut"
            ;;
    esac
    
    # Vérification
    verify_deployment
    
    # Redémarrage conditionnel
    if [ "$NO_RESTART" = false ]; then
        restart_keycloak
    else
        log_info "Redémarrage ignoré (--no-restart)"
    fi
    
    # Messages finaux
    echo
    log_success "✅ Déploiement terminé avec succès!"
    echo
    log_info "📋 Prochaines étapes:"
    echo "   1. Connectez-vous à la console d'administration Keycloak"
    echo "   2. Allez dans 'Realm Settings' > 'Themes'"
    echo "   3. Sélectionnez '$THEME_NAME' pour 'Login Theme'"
    echo "   4. Cliquez sur 'Save'"
    echo
    log_info "🌐 Console d'administration: http://localhost:8080/admin"
    echo
}

# Exécution du script principal
main "$@"
