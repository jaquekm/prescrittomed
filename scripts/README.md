# Scripts Utilitários - SmartRx AI

Este diretório contém scripts Python para operações administrativas e de manutenção do sistema.

## 📋 Scripts Disponíveis

### `seed_database.py`

Script para popular o banco de dados com dados iniciais (seed data).

**Uso:**
```bash
python scripts/seed_database.py
```

**O que faz:**
- Conecta ao banco de dados PostgreSQL usando SQLAlchemy
- Insere 3 itens na tabela `knowledge_base`:
  1. **Amoxicilina 500mg** (DRUG_LEAFLET)
  2. **Protocolo de Amigdalite Bacteriana** (OFFICIAL_PROTOCOL)
  3. **Dipirona 1g** (DRUG_LEAFLET)
- Gera embeddings fake (1536 floats aleatórios) para cada item
- Valida a inserção e exibe estatísticas

**Pré-requisitos:**
- Container Docker com PostgreSQL rodando
- Variáveis de ambiente configuradas (`.env` ou variáveis do sistema)
- Dependências instaladas: `pip install -r requirements.txt`

**Exemplo de saída:**
```
🌱 Iniciando seed do banco de dados...
------------------------------------------------------------
📊 Conectando ao banco de dados...
   Host: localhost:5432
✅ Conectado ao PostgreSQL
   Versão: PostgreSQL 16.x

📝 Preparando 3 itens para inserção...

   ✓ Bula - Amoxicilina 500mg (DRUG_LEAFLET)
   ✓ PCDT - Amigdalite Bacteriana (OFFICIAL_PROTOCOL)
   ✓ Bula - Dipirona 1g (DRUG_LEAFLET)

✅ 3 itens inseridos com sucesso!

📊 Total de itens na knowledge_base: 3
🔒 Conexão fechada.
```

**Troubleshooting:**

1. **Erro de conexão:**
   - Verifique se o container está rodando: `docker-compose ps`
   - Verifique as credenciais no arquivo `.env`
   - Teste a conexão: `python check_db.py`

2. **Erro de dependências:**
   ```bash
   pip install sqlalchemy pgvector python-decouple psycopg2-binary
   ```

3. **Tabela não encontrada:**
   - Execute o script de inicialização SQL primeiro
   - Verifique se o container foi iniciado: `docker-compose up -d`

## 🔧 Desenvolvimento

Para adicionar novos scripts:

1. Crie o arquivo Python no diretório `scripts/`
2. Use o mesmo padrão de conexão do `seed_database.py`
3. Adicione documentação neste README
4. Teste o script antes de commitar
