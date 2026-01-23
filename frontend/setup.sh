#!/bin/bash
# Script de setup rápido para o frontend

echo "🚀 Configurando frontend SmartRx AI..."
echo ""

# Verifica se Node.js está instalado
if ! command -v node &> /dev/null; then
    echo "❌ Node.js não está instalado. Por favor, instale o Node.js 18+ primeiro."
    exit 1
fi

# Verifica se npm está instalado
if ! command -v npm &> /dev/null; then
    echo "❌ npm não está instalado. Por favor, instale o npm primeiro."
    exit 1
fi

echo "✅ Node.js e npm encontrados"
echo ""

# Instala dependências
echo "📦 Instalando dependências..."
npm install

echo ""
echo "📝 Configurando variáveis de ambiente..."

# Cria .env.local se não existir
if [ ! -f .env.local ]; then
    cp .env.local.example .env.local
    echo "✅ Arquivo .env.local criado"
    echo "   Por favor, edite-o se necessário"
else
    echo "✅ Arquivo .env.local já existe"
fi

echo ""
echo "✅ Setup concluído!"
echo ""
echo "🚀 Para iniciar o servidor:"
echo "   npm run dev"
echo ""
echo "📚 Acesse: http://localhost:3000"
