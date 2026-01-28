# 🚀 Quick Start - Frontend SmartRx AI

## Instalação Rápida

```bash
# 1. Instalar dependências
cd frontend
npm install

# 2. Configurar variáveis de ambiente
cp .env.local.example .env.local
# Edite .env.local e configure NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. Iniciar servidor
npm run dev
```

## Acessar

Abra: http://localhost:3000

## Testar

1. Digite "Amigdalite" no campo de sintomas
2. Clique em "Gerar Prescrição"
3. Veja os cards de medicamentos aparecerem!

## Pré-requisitos

- Node.js 18+ instalado
- Backend FastAPI rodando em http://localhost:8000
- Banco de dados populado (execute `python scripts/seed_database.py`)
