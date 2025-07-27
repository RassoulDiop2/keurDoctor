@echo off
echo.
echo 🏥 DIAGNOSTIC COMPLET SYSTÈME KEURDOCTOR
echo =======================================
echo.
cd /d "h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app"
echo 🔍 Lancement du diagnostic...
echo.
.\KDenv\Scripts\python.exe manage.py diagnostic_complet
echo.
echo ✅ Diagnostic terminé!
echo.
echo 📋 Pour tester spécifiquement AuditLog :
echo    .\KDenv\Scripts\python.exe manage.py test_auditlog_correction
echo.
pause
