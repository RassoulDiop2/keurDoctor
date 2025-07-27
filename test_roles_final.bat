@echo off
echo.
echo 🎭 TEST COMPLET RÔLES KEYCLOAK
echo ==============================
echo.
echo ⚠️  IMPORTANT: Assurez-vous que Keycloak est démarré sur localhost:8080
echo.
cd /d "h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app"

echo 🔍 1. Test rapide des méthodes...
.\KDenv\Scripts\python.exe test_roles_rapide.py

echo.
echo 🧪 2. Test complet rôles realm + client + groupes...
.\KDenv\Scripts\python.exe test_roles_complet.py

echo.
echo ✅ Tests terminés!
pause
