# Script PowerShell pour appliquer les migrations
Write-Host "🔧 Application des migrations KeurDoctor..." -ForegroundColor Cyan

# Vérifier l'état des migrations
Write-Host "`n📋 État actuel des migrations:" -ForegroundColor Yellow
try {
    & python.exe manage.py showmigrations comptes
}
catch {
    Write-Host "❌ Erreur lors de la vérification des migrations: $_" -ForegroundColor Red
}

# Appliquer toutes les migrations
Write-Host "`n🚀 Application de toutes les migrations..." -ForegroundColor Green
try {
    & python.exe manage.py migrate
    Write-Host "✅ Migrations appliquées avec succès!" -ForegroundColor Green
    
    Write-Host "`n🎯 PROCHAINES ÉTAPES:" -ForegroundColor Cyan
    Write-Host "1. Redémarrer le serveur Django" -ForegroundColor White
    Write-Host "2. Tester l'ACCÈS RFID UNIVERSEL" -ForegroundColor White
    Write-Host "3. Vérifier que les erreurs AuditLog ont disparu" -ForegroundColor White
    
}
catch {
    Write-Host "❌ Erreur lors de l'application des migrations: $_" -ForegroundColor Red
    
    Write-Host "`n🔍 DÉBOGAGE:" -ForegroundColor Yellow
    Write-Host "Essayez d'appliquer les migrations une par une:" -ForegroundColor White
    Write-Host "python.exe manage.py migrate comptes 0010" -ForegroundColor Gray
    Write-Host "python.exe manage.py migrate comptes 0011" -ForegroundColor Gray
}

Write-Host "`nAppuyez sur une touche pour continuer..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
