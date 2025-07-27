@echo off
echo 🧪 LANCEMENT DU TEST CORRECTION AUDITLOG
echo ======================================
cd /d "h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app"
.\KDenv\Scripts\python.exe manage.py test_auditlog_correction
echo.
echo ✅ Test terminé!
pause
