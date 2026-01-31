# Frontend Next.js - SmartRx AI

Frontend React/Next.js para o sistema SmartRx AI com interface de geração de prescrições médicas.

## 🚀 Início Rápido

### 1. Instalar dependências

```bash
cd frontend
npm install
```

### 2. Configurar variáveis de ambiente

Copie o arquivo de exemplo e configure:

```bash
cp .env.local.example .env.local
```

Edite `.env.local` e configure:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Iniciar o servidor de desenvolvimento

```bash
npm run dev
```

O frontend estará disponível em: http://localhost:3000

## 📋 Estrutura do Projeto

```
frontend/
├── app/
│   ├── layout.tsx          # Layout raiz
│   ├── page.tsx            # Página Cockpit (principal)
│   └── globals.css         # Estilos globais + Tailwind
├── components/
│   ├── PrescriptionInput.tsx    # Input de sintomas/diagnóstico
│   ├── MedicationCard.tsx       # Card individual de medicamento
│   ├── MedicationCards.tsx      # Container de cards
│   └── Toast.tsx                # Notificação de erros
├── types/
│   └── prescription.ts    # Tipos TypeScript
└── package.json
```

## 🎨 Layout Cockpit

O layout é dividido em **30/70**:

- **30% (Esquerda)**: Painel de input com formulário de sintomas/diagnóstico
- **70% (Direita)**: Área de resultados com cards de medicamentos

## 🔌 Integração com Backend

O frontend se conecta ao backend FastAPI através do endpoint:
- `POST /api/v1/prescribe`

A URL do backend é configurada via variável de ambiente `NEXT_PUBLIC_API_URL`.

## 🧪 Funcionalidades

### ✅ Implementado

- ✅ Layout 30/70 responsivo
- ✅ Input de sintomas e diagnóstico
- ✅ Conexão com API FastAPI
- ✅ Renderização de cards de medicamentos
- ✅ Toast de erro (vermelho) para falhas
- ✅ Loading state durante requisição
- ✅ Validação de formulário

### 📦 Componentes

1. **PrescriptionInput**: Formulário de entrada
2. **MedicationCard**: Card individual de medicamento
3. **MedicationCards**: Container com todas as informações da prescrição
4. **Toast**: Notificação de erros (fecha automaticamente após 5s)

## 🎯 Critério de Sucesso

1. Abrir http://localhost:3000
2. Digitar "Amigdalite" no campo de sintomas
3. Clicar em "Gerar Prescrição"
4. Ver cards de medicamentos aparecerem em menos de 5 segundos

## 🐛 Troubleshooting

### Erro de CORS

Se houver erro de CORS, verifique se o backend FastAPI tem CORS configurado para aceitar requisições de `http://localhost:3000`.

### Erro de conexão

- Verifique se o backend está rodando: `python run_api.py`
- Verifique a URL no `.env.local`
- Teste a API diretamente: `curl http://localhost:8000/health`

### Erro de build

```bash
# Limpar cache e reinstalar
rm -rf .next node_modules
npm install
npm run dev
```

## 📝 Scripts Disponíveis

- `npm run dev` - Inicia servidor de desenvolvimento
- `npm run build` - Build para produção
- `npm run start` - Inicia servidor de produção
- `npm run lint` - Executa linter
