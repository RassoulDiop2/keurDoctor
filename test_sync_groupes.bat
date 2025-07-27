@echo off
echo.
echo 🏥 TEST SYNCHRONISATION KEYCLOAK COMPLÈTE
echo ========================================
echo.
echo ⚠️  IMPORTANT: Assurez-vous que Keycloak est démarré sur localhost:8080
echo.
cd /d "h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app"

echo 🔍 1. Diagnostic des signaux Django...
.\KDenv\Scripts\python.exe diagnostic_signaux.py

echo.
echo 🧪 2. Test complet de synchronisation...
.\KDenv\Scripts\python.exe test_sync_complete.py

echo.
echo ✅ Tests terminés!
pause
