@echo off
echo 🚀 DÉMARRAGE DE KEURDOCTOR
echo ============================

REM Activation de l'environnement virtuel
if exist "KDenv\Scripts\activate.bat" (
    echo ✅ Activation de l'environnement virtuel...
    call KDenv\Scripts\activate.bat
) else (
    echo ⚠️  Environnement virtuel non trouvé
)

REM Application des migrations
echo ✅ Application des migrations...
python manage.py migrate

REM Démarrage du serveur
echo ✅ Démarrage du serveur Django...
echo 🌐 Serveur disponible sur: http://127.0.0.1:8000
echo 📋 Interface admin: http://127.0.0.1:8000/admin
echo 🛑 Pour arrêter: Ctrl+C
echo.
python manage.py runserver 0.0.0.0:8000

pause
