#!/bin/bash

# Script de déploiement du thème Keycloak CHIFT
# Copie les fichiers du thème dans le container Docker Keycloak
# et redémarre le service pour appliquer les changements

set -e

echo "[INFO] 🚀 Démarrage du déploiement du thème Keycloak CHIFT"

# Vérifier que Docker est disponible
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker n'est pas installé ou pas disponible dans le PATH"
    exit 1
fi

echo "[SUCCESS] Docker est disponible"

# Définir les chemins
THEME_DIR="chift-theme"
CONTAINER_NAME="chiftbackend-keycloak-1"

# Vérifier que le dossier du thème existe
if [ ! -d "$THEME_DIR" ]; then
    echo "[ERROR] Le dossier du thème $THEME_DIR n'existe pas!"
    echo "[INFO] Veuillez exécuter ce script depuis le dossier keycloak-themes/"
    exit 1
fi

echo "[SUCCESS] Dossier du thème trouvé: $THEME_DIR"

# Vérifier que le container Keycloak existe
if ! docker ps -a --format "table {{.Names}}" | grep -q "$CONTAINER_NAME"; then
    echo "[ERROR] Container Keycloak '$CONTAINER_NAME' introuvable"
    echo "[INFO] Vérifiez que Docker Compose est lancé"
    exit 1
fi

echo "[SUCCESS] Container Keycloak trouvé: $CONTAINER_NAME"

# Copier le thème dans le container
echo "[INFO] 📁 Copie du thème dans le container..."
if docker cp "$THEME_DIR" "$CONTAINER_NAME:/opt/keycloak/themes/"; then
    echo "[SUCCESS] Thème copié avec succès"
else
    echo "[ERROR] Erreur lors de la copie du thème"
    exit 1
fi

# Vérifier que les fichiers ont été copiés
echo "[INFO] 🔍 Vérification de la copie..."
if docker exec "$CONTAINER_NAME" test -d "/opt/keycloak/themes/chift-theme"; then
    echo "[SUCCESS] Thème présent dans le container"
else
    echo "[ERROR] Thème non trouvé dans le container"
    exit 1
fi

# Redémarrer Keycloak
echo "[INFO] 🔄 Redémarrage de Keycloak..."
cd ..
if docker-compose restart keycloak; then
    echo "[SUCCESS] Keycloak redémarré avec succès"
else
    echo "[ERROR] Erreur lors du redémarrage de Keycloak"
    exit 1
fi

echo ""
echo "🎉 Déploiement terminé avec succès!"
echo "=================================="
echo ""
echo "📝 Prochaines étapes :"
echo "1. Attendre 30-60 secondes que Keycloak redémarre"
echo "2. Aller dans l'Admin Console: http://localhost:8080/admin/"
echo "3. Naviguer vers: Realm Settings > Themes"
echo "4. Définir tous les thèmes sur 'chift-theme':"
echo "   - Login theme: chift-theme"
echo "   - Account theme: chift-theme"
echo "   - Email theme: chift-theme"
echo "5. Cliquer sur 'Save'"
echo ""
echo "🌐 URLs de test :"
echo "- Admin Console: http://localhost:8080/admin/"
echo "- Test login: http://localhost:8080/realms/chift/protocol/openid_connect/auth?client_id=account&redirect_uri=http://localhost:8080/realms/chift/account&response_type=code"
echo ""
echo "✨ Le thème CHIFT est maintenant déployé!"
