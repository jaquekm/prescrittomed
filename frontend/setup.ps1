# Script de setup rápido para o frontend (PowerShell)
# Para Windows

Write-Host "🚀 Configurando frontend SmartRx AI..." -ForegroundColor Cyan
Write-Host ""

# Verifica se Node.js está instalado
try {
    $nodeVersion = node --version
    Write-Host "✅ Node.js encontrado: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Node.js não está instalado. Por favor, instale o Node.js 18+ primeiro." -ForegroundColor Red
    exit 1
}

# Verifica se npm está instalado
try {
    $npmVersion = npm --version
    Write-Host "✅ npm encontrado: v$npmVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ npm não está instalado. Por favor, instale o npm primeiro." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
npm install

Write-Host ""
Write-Host "📝 Configurando variáveis de ambiente..." -ForegroundColor Yellow

# Cria .env.local se não existir
if (-not (Test-Path .env.local)) {
    Copy-Item .env.local.example .env.local
    Write-Host "✅ Arquivo .env.local criado" -ForegroundColor Green
    Write-Host "   Por favor, edite-o se necessário" -ForegroundColor Yellow
} else {
    Write-Host "✅ Arquivo .env.local já existe" -ForegroundColor Green
}

Write-Host ""
Write-Host "✅ Setup concluído!" -ForegroundColor Green
Write-Host ""
Write-Host "🚀 Para iniciar o servidor:" -ForegroundColor Cyan
Write-Host "   npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "📚 Acesse: http://localhost:3000" -ForegroundColor Cyan
