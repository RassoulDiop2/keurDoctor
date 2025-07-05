#!/bin/bash

# Script de vérification du thème CHIFT
# Vérifie que tous les fichiers sont présents et correctement configurés

echo "🔍 Vérification du thème CHIFT Keycloak"
echo "========================================"

THEME_DIR="/Users/User/Desktop/Mes_Projets/service_chift/CHIFT/chiftbackend/keycloak-themes/chift-theme"
MISSING_FILES=0

# Fonction pour vérifier l'existence d'un fichier
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1"
    else
        echo "❌ $1 - MANQUANT"
        ((MISSING_FILES++))
    fi
}

# Fonction pour vérifier l'existence d'un dossier
check_dir() {
    if [ -d "$1" ]; then
        echo "📁 $1"
    else
        echo "❌ $1 - DOSSIER MANQUANT"
        ((MISSING_FILES++))
    fi
}

echo ""
echo "📋 Vérification de la structure du thème..."

# Vérification des dossiers principaux
check_dir "$THEME_DIR"
check_dir "$THEME_DIR/login"
check_dir "$THEME_DIR/account"
check_dir "$THEME_DIR/email"
check_dir "$THEME_DIR/resources"
check_dir "$THEME_DIR/resources/css"
check_dir "$THEME_DIR/resources/img"

echo ""
echo "📄 Vérification des fichiers de configuration..."

# Fichiers de configuration
check_file "$THEME_DIR/theme.properties"
check_file "$THEME_DIR/login/theme.properties"
check_file "$THEME_DIR/account/theme.properties"
check_file "$THEME_DIR/email/theme.properties"

echo ""
echo "🎨 Vérification des templates..."

# Templates login
check_file "$THEME_DIR/login/template.ftl"
check_file "$THEME_DIR/login/login.ftl"
check_file "$THEME_DIR/login/login-reset-password.ftl"
check_file "$THEME_DIR/login/login-update-password.ftl"
check_file "$THEME_DIR/login/update-password.ftl"
check_file "$THEME_DIR/login/error.ftl"
check_file "$THEME_DIR/login/login-otp.ftl"
check_file "$THEME_DIR/login/login-verify-email.ftl"

# Templates account
check_file "$THEME_DIR/account/account.ftl"
check_file "$THEME_DIR/account/template.ftl"

# Templates email
check_file "$THEME_DIR/email/html/email-verification.ftl"

echo ""
echo "🌐 Vérification des messages..."

# Messages
check_file "$THEME_DIR/login/messages/messages_fr.properties"

echo ""
echo "🖼️  Vérification des ressources..."

# Ressources
check_file "$THEME_DIR/resources/css/style.css"
check_file "$THEME_DIR/resources/img/logo_placeholder.svg"
check_file "$THEME_DIR/resources/img/favicon.ico"

echo ""
echo "🔧 Vérification du contenu des fichiers critiques..."

# Vérification du contenu du template principal
if [ -f "$THEME_DIR/login/template.ftl" ]; then
    if grep -q "chift-blue" "$THEME_DIR/login/template.ftl"; then
        echo "✅ Couleurs CHIFT présentes dans template.ftl"
    else
        echo "⚠️  Couleurs CHIFT manquantes dans template.ftl"
    fi
    
    if grep -q "logo_placeholder.svg" "$THEME_DIR/login/template.ftl"; then
        echo "✅ Logo intégré dans template.ftl"
    else
        echo "⚠️  Logo non intégré dans template.ftl"
    fi
    
    if grep -q "CHIFT. Tous droits réservés" "$THEME_DIR/login/template.ftl"; then
        echo "✅ Footer copyright présent"
    else
        echo "⚠️  Footer copyright manquant"
    fi
    
    if grep -q "@media (max-width: 640px)" "$THEME_DIR/login/template.ftl"; then
        echo "✅ Media queries responsive présentes"
    else
        echo "⚠️  Media queries responsive manquantes"
    fi
fi

echo ""
echo "🐳 Vérification Docker..."

# Vérification que Keycloak est en cours d'exécution
if docker ps | grep -q "keycloak"; then
    echo "✅ Container Keycloak en cours d'exécution"
else
    echo "⚠️  Container Keycloak non démarré"
fi

echo ""
echo "📊 Résumé de la vérification"
echo "============================"

if [ $MISSING_FILES -eq 0 ]; then
    echo "🎉 Tous les fichiers sont présents !"
    echo "✅ Thème CHIFT prêt pour l'utilisation"
    echo ""
    echo "📝 Prochaines étapes :"
    echo "1. Déployez avec : ./deploy-theme.sh"
    echo "2. Testez avec : ./test-theme.sh"
    echo "3. Configurez le realm Keycloak pour utiliser 'chift-theme'"
else
    echo "❌ $MISSING_FILES fichier(s) manquant(s)"
    echo "🔧 Veuillez créer les fichiers manquants avant de continuer"
fi

echo ""
echo "🌐 URLs utiles :"
echo "- Admin Console: http://localhost:8080/admin/"
echo "- Test login: http://localhost:8080/realms/chift/protocol/openid_connect/auth?client_id=account&redirect_uri=http://localhost:8080/realms/chift/account&response_type=code"
