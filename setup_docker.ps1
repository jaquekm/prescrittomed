# Script de setup rápido para Docker - SmartRx AI (PowerShell)
# Para Windows

Write-Host "🚀 Configurando infraestrutura Docker para SmartRx AI..." -ForegroundColor Cyan
Write-Host ""

# Verifica se Docker está instalado
try {
    docker --version | Out-Null
} catch {
    Write-Host "❌ Docker não está instalado. Por favor, instale o Docker Desktop primeiro." -ForegroundColor Red
    exit 1
}

# Verifica se Docker Compose está instalado
try {
    docker-compose --version | Out-Null
} catch {
    Write-Host "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro." -ForegroundColor Red
    exit 1
}

# Cria arquivo .env se não existir
if (-not (Test-Path .env)) {
    Write-Host "📝 Criando arquivo .env a partir do .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "✅ Arquivo .env criado. Por favor, edite-o com suas configurações." -ForegroundColor Green
} else {
    Write-Host "✅ Arquivo .env já existe." -ForegroundColor Green
}

Write-Host ""
Write-Host "🐳 Iniciando containers Docker..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "⏳ Aguardando PostgreSQL ficar pronto..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "🔍 Verificando conexão..." -ForegroundColor Cyan
python check_db.py

Write-Host ""
Write-Host "✅ Setup concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "📚 Para mais informações, consulte README_DOCKER.md" -ForegroundColor Cyan
