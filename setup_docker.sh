#!/bin/bash
# Script de setup rápido para Docker - SmartRx AI

set -e

echo "🚀 Configurando infraestrutura Docker para SmartRx AI..."
echo ""

# Verifica se Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não está instalado. Por favor, instale o Docker primeiro."
    exit 1
fi

# Verifica se Docker Compose está instalado
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não está instalado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Cria arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env a partir do .env.example..."
    cp .env.example .env
    echo "✅ Arquivo .env criado. Por favor, edite-o com suas configurações."
else
    echo "✅ Arquivo .env já existe."
fi

echo ""
echo "🐳 Iniciando containers Docker..."
docker-compose up -d

echo ""
echo "⏳ Aguardando PostgreSQL ficar pronto..."
sleep 5

echo ""
echo "🔍 Verificando conexão..."
python check_db.py

echo ""
echo "✅ Setup concluído!"
echo ""
echo "📚 Para mais informações, consulte README_DOCKER.md"
