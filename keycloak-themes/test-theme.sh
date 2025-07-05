#!/bin/bash

# Script de test pour vérifier le thème CHIFT Keycloak
# Ce script ouvre plusieurs onglets avec différentes tailles d'écran pour tester la responsivité

echo "🚀 Test du thème CHIFT Keycloak"
echo "================================"

KEYCLOAK_URL="http://localhost:8080"
REALM="chift"

echo "📋 URLs de test :"
echo "- Page de connexion: ${KEYCLOAK_URL}/realms/${REALM}/protocol/openid_connect/auth?client_id=account&redirect_uri=${KEYCLOAK_URL}/realms/${REALM}/account&response_type=code"
echo "- Admin Console: ${KEYCLOAK_URL}/admin/master/console/"

echo ""
echo "🎨 Vérifications à effectuer :"
echo "- ✅ Logo CHIFT affiché"
echo "- ✅ Couleurs CHIFT (#0E6B85, #037ea0, #0491b8)"
echo "- ✅ Design responsive (mobile/tablet/desktop)"
echo "- ✅ Footer \"© 2025 CHIFT. Tous droits réservés\""
echo "- ✅ Messages d'erreur modernes"
echo "- ✅ Formulaires avec placeholders français"

echo ""
echo "📱 Tests de responsivité recommandés :"
echo "- Mobile : 375px x 667px (iPhone)"
echo "- Tablet : 768px x 1024px (iPad)"
echo "- Desktop : 1200px x 800px"

echo ""
echo "🌐 Ouvrez votre navigateur et testez ces URLs..."

# Optionnel : ouvrir automatiquement dans le navigateur par défaut
# uncomment the line below if you want to auto-open
# open "${KEYCLOAK_URL}/realms/${REALM}/protocol/openid_connect/auth?client_id=account&redirect_uri=${KEYCLOAK_URL}/realms/${REALM}/account&response_type=code"
