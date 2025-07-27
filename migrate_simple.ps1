Write-Host "Application des migrations KeurDoctor..." -ForegroundColor Cyan

Write-Host "État des migrations:" -ForegroundColor Yellow
python.exe manage.py showmigrations comptes

Write-Host "Application des migrations..." -ForegroundColor Green
python.exe manage.py migrate

Write-Host "Migrations terminées!" -ForegroundColor Green
