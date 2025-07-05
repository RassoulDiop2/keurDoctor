
#!/bin/bash
set -e

echo "🚀 Démarrage de KeurDoctor..."

# Couleurs pour les messages
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Nettoyer et démarrer
print_status "Nettoyage des conteneurs existants..."
docker-compose down --remove-orphans 2>/dev/null || true

print_status "Démarrage des services..."
docker-compose up --build -d

# Attendre que les services soient prêts
print_status "Attente du démarrage des services..."
sleep 15

# Vérifier l'état des services
print_status "Vérification de l'état des services..."

if curl -f http://localhost:8000 >/dev/null 2>&1; then
    print_status "✅ Django est opérationnel sur http://localhost:8000"
else
    print_warning "⚠️  Django n'est pas encore prêt"
fi

if curl -f http://localhost:8080/health/live >/dev/null 2>&1; then
    print_status "✅ Keycloak est opérationnel sur http://localhost:8080"
else
    print_warning "⚠️  Keycloak n'est pas encore prêt (peut prendre quelques minutes)"
fi

echo ""
print_status "🎉 Services démarrés!"
echo "📱 Application: http://localhost:8000"
echo "🔧 Keycloak Admin: http://localhost:8080/admin (admin/admin)"
echo ""
print_status "Commandes utiles:"
echo "- Voir les logs: docker-compose logs -f"
echo "- Arrêter: docker-compose down"
echo "- Redémarrer: docker-compose restart"
