#!/bin/bash

echo "🛑 Arrêt de KeurDoctor..."

# Couleurs pour les messages
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Arrêter Django local s'il fonctionne
if [ -f ".django_pid" ]; then
    DJANGO_PID=$(cat .django_pid)
    if ps -p $DJANGO_PID > /dev/null; then
        print_status "Arrêt de Django (PID: $DJANGO_PID)..."
        kill $DJANGO_PID
        sleep 2
        
        # Force kill si nécessaire
        if ps -p $DJANGO_PID > /dev/null; then
            print_warning "Force kill de Django..."
            kill -9 $DJANGO_PID
        fi
    fi
    rm -f .django_pid
fi

# Arrêter les conteneurs Docker
print_status "Arrêt des conteneurs Docker..."
docker-compose down --remove-orphans

print_status "✅ KeurDoctor arrêté proprement."
