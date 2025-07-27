@echo off
REM Script pour tester la correction AuditLog
cd /d "h:\SRT3\PSFE\ProjetSoutenance_SASPM\KeurDoctor\keur_Doctor_app"
echo Activation de l'environnement virtuel...
call .\KDenv\Scripts\activate.bat
echo Lancement du test AuditLog...
python test_auditlog_fix.py
pause
