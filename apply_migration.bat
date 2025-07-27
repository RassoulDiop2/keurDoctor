@echo off
echo 🔧 Application de la migration AuditLog session_id...
python.exe manage.py migrate comptes 0011_fix_auditlog_session_id
if %ERRORLEVEL% == 0 (
    echo ✅ Migration appliquée avec succès!
    echo.
    echo 📋 Application de toutes les migrations restantes...
    python.exe manage.py migrate
    if %ERRORLEVEL% == 0 (
        echo ✅ Toutes les migrations appliquées!
        echo.
        echo 🎯 PROCHAINES ÉTAPES:
        echo 1. Redémarrer le serveur Django
        echo 2. Tester l'ACCÈS RFID UNIVERSEL
        echo 3. Vérifier que les erreurs AuditLog ont disparu
    ) else (
        echo ❌ Erreur lors de l'application des migrations
    )
) else (
    echo ❌ Erreur lors de l'application de la migration session_id
)
pause
