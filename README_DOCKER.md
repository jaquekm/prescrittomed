# 🐳 Infraestrutura Docker - SmartRx AI

Este guia explica como configurar e usar a infraestrutura Docker para o projeto SmartRx AI.

## 📋 Pré-requisitos

- Docker e Docker Compose instalados
- Python 3.8+ (para o script de verificação)
- Dependências Python: `psycopg2-binary`, `python-decouple`

## 🚀 Configuração Rápida

### 1. Criar arquivo `.env`

Copie o arquivo de exemplo e ajuste as variáveis conforme necessário:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e configure:
- Credenciais do PostgreSQL
- Chave secreta do Django
- Chave da API OpenAI (se disponível)

### 2. Iniciar o banco de dados

```bash
docker-compose up -d
```

Isso irá:
- Baixar a imagem `pgvector/pgvector:pg16`
- Criar o container PostgreSQL
- Executar automaticamente o script `core/sql/init_db.sql`
- Criar todas as tabelas, índices e views necessárias

### 3. Verificar a conexão

```bash
python check_db.py
```

Você deve ver a mensagem:
```
✅ Conexão OK: Tabelas [doctors, knowledge_base, consultations, prescriptions, audit_logs] encontradas
```

## 📊 Estrutura do Banco de Dados

O script de inicialização cria:

### Tabelas Principais

1. **`doctors`** - Médicos cadastrados
2. **`knowledge_base`** - Base de conhecimento vetorizada (RAG)
   - Armazena chunks de bulas e protocolos
   - Suporta busca semântica via embeddings
3. **`consultations`** - Consultas médicas
4. **`prescriptions`** - Prescrições geradas
   - Campos críticos: `is_ai_generated`, `was_edited_by_doctor`
5. **`audit_logs`** - Logs de auditoria (compliance)

### Views

- **`prescriptions_with_traceability`** - Prescrições com rastreabilidade completa
- **`ai_usage_stats`** - Estatísticas de uso da IA

### Extensões PostgreSQL

- **`vector`** - Suporte a vetores para busca semântica
- **`uuid-ossp`** - Geração de UUIDs

## 🔧 Comandos Úteis

### Ver logs do container

```bash
docker-compose logs -f postgres
```

### Parar o container

```bash
docker-compose down
```

### Parar e remover volumes (⚠️ apaga dados)

```bash
docker-compose down -v
```

### Conectar ao banco via psql

```bash
docker-compose exec postgres psql -U prescrittomed -d prescrittomed_db
```

### Verificar status

```bash
docker-compose ps
```

## 🐛 Troubleshooting

### Container não inicia

1. Verifique se a porta 5432 está livre:
   ```bash
   netstat -an | grep 5432
   ```
2. Altere a porta no `.env` se necessário:
   ```
   POSTGRES_PORT=5433
   ```

### Script de inicialização não executou

1. Verifique os logs:
   ```bash
   docker-compose logs postgres
   ```
2. Execute o script manualmente:
   ```bash
   docker-compose exec postgres psql -U prescrittomed -d prescrittomed_db -f /docker-entrypoint-initdb.d/01_init_schema.sql
   ```

### Erro de conexão no check_db.py

1. Verifique se o container está rodando:
   ```bash
   docker-compose ps
   ```
2. Verifique as variáveis de ambiente no `.env`
3. Teste a conexão manualmente:
   ```bash
   docker-compose exec postgres psql -U prescrittomed -d prescrittomed_db -c "SELECT version();"
   ```

## 📝 Notas Importantes

- O script `init_db.sql` usa `CREATE TABLE IF NOT EXISTS` para permitir execuções múltiplas sem erros
- Os dados persistem em um volume Docker chamado `postgres_data`
- Para desenvolvimento, você pode usar SQLite, mas para produção use PostgreSQL com pgvector

## 🔒 Segurança

⚠️ **IMPORTANTE**: O arquivo `.env` contém credenciais sensíveis e está no `.gitignore`. Nunca commite este arquivo no repositório.

Para produção:
- Use senhas fortes
- Configure SSL/TLS para conexões
- Use variáveis de ambiente do sistema ou um gerenciador de secrets
