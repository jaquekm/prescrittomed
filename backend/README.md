# Backend FastAPI - SmartRx AI

API REST para geração de prescrições médicas assistidas por IA usando RAG (Retrieval-Augmented Generation).

## 🚀 Início Rápido

### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Certifique-se de que o arquivo `.env` está configurado com:
- `OPENAI_API_KEY` - Chave da API OpenAI
- `DATABASE_URL` ou variáveis individuais do PostgreSQL
- Outras variáveis necessárias (veja `.env.example`)

### 3. Iniciar o servidor

```bash
python run_api.py
```

Ou usando uvicorn diretamente:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acessar a documentação

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📋 Endpoints

### `GET /`
Informações básicas da API.

### `GET /health`
Health check do serviço.

### `POST /api/v1/prescribe`
Gera uma prescrição médica baseada em sintomas e diagnóstico.

**Request Body:**
```json
{
  "symptoms": "Dor de garganta, febre e dificuldade para engolir",
  "diagnosis": "Amigdalite bacteriana"
}
```

**Response:**
```json
{
  "medicamentos": [
    {
      "nome": "Amoxicilina",
      "principio_ativo": "Amoxicilina",
      "forma": "Cápsula",
      "concentracao": "500mg",
      "posologia": "1 cápsula",
      "via": "Oral",
      "frequencia": "A cada 8 horas",
      "duracao": "10 dias",
      "observacoes": "Tomar após refeições"
    }
  ],
  "resumo_tecnico_medico": [
    "Tratamento de primeira linha para amigdalite bacteriana"
  ],
  "orientacoes_ao_paciente": [
    "Completar o tratamento mesmo com melhora dos sintomas"
  ],
  "alertas_seguranca": [],
  "monitorizacao": [],
  "fontes": [
    {
      "source_id": "pcdt_amigdalite_001",
      "source_type": "OFFICIAL_PROTOCOL",
      "title": "PCDT - Amigdalite Bacteriana",
      "confidence_score": 0.85
    }
  ],
  "confidence_score": 0.85
}
```

## 🔧 Como Funciona

1. **Geração de Embedding**: O sistema gera um vetor de embedding (1536 dimensões) para os sintomas/diagnóstico usando OpenAI `text-embedding-3-small`.

2. **Busca Semântica**: Busca no banco de dados `knowledge_base` usando similaridade de cosseno (pgvector).

3. **Geração de Prescrição**: Envia o contexto encontrado para GPT-4o, que gera a prescrição estruturada baseada nos protocolos oficiais.

4. **Rastreabilidade**: Todas as fontes consultadas são incluídas na resposta com scores de confiança.

## 🧪 Testes

Execute os testes unitários:

```bash
pytest tests/test_api.py -v
```

Ou todos os testes:

```bash
pytest tests/ -v
```

## 📊 Estrutura

```
backend/
├── __init__.py
├── main.py              # Aplicação FastAPI principal
├── schemas.py           # Schemas Pydantic (request/response)
└── services/
    ├── __init__.py
    └── rag_service.py   # Serviço RAG (busca + geração)
```

## ⚠️ Importante

- **Sistema de Apoio**: Esta é uma ferramenta de APOIO à decisão médica. O médico é sempre o responsável final.
- **Compliance**: Sistema desenvolvido seguindo ANVISA RDC 657/2022 e LGPD.
- **Determinístico**: LLM configurado com `temperature=0.0` para respostas determinísticas.

## 🐛 Troubleshooting

### Erro: "RAG Service não disponível"
- Verifique se o banco de dados está rodando: `docker-compose ps`
- Verifique as credenciais no `.env`

### Erro: "Não foram encontrados protocolos clínicos"
- Execute o script de seed: `python scripts/seed_database.py`
- Verifique se há dados na tabela `knowledge_base`

### Erro de conexão com OpenAI
- Verifique se `OPENAI_API_KEY` está configurada
- Teste a chave manualmente
