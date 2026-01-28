#!/usr/bin/env python3
"""
Script para verificar conexão com o banco de dados PostgreSQL
e listar as tabelas criadas pelo schema de inicialização.
"""

import os
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importar decouple
sys.path.insert(0, str(Path(__file__).parent))

try:
    from decouple import config
    import psycopg2
    from psycopg2 import sql
except ImportError as e:
    print(f"❌ Erro: Dependências não instaladas. Execute: pip install python-decouple psycopg2-binary")
    print(f"   Detalhes: {e}")
    sys.exit(1)


def get_db_config():
    """Obtém configuração do banco de dados das variáveis de ambiente"""
    # Tenta usar DATABASE_URL primeiro, depois variáveis individuais
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Parse da URL do formato postgresql://user:pass@host:port/db
        from urllib.parse import urlparse
        parsed = urlparse(database_url)
        return {
            'host': parsed.hostname or config('POSTGRES_HOST', default='localhost'),
            'port': parsed.port or config('POSTGRES_PORT', default=5432, cast=int),
            'database': parsed.path.lstrip('/') or config('POSTGRES_DB', default='prescrittomed_db'),
            'user': parsed.username or config('POSTGRES_USER', default='prescrittomed'),
            'password': parsed.password or config('POSTGRES_PASSWORD', default='prescrittomed_pass'),
        }
    
    # Fallback para variáveis individuais
    return {
        'host': config('POSTGRES_HOST', default='localhost'),
        'port': config('POSTGRES_PORT', default=5432, cast=int),
        'database': config('POSTGRES_DB', default='prescrittomed_db'),
        'user': config('POSTGRES_USER', default='prescrittomed'),
        'password': config('POSTGRES_PASSWORD', default='prescrittomed_pass'),
    }


def check_extensions(conn):
    """Verifica se as extensões necessárias estão instaladas"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT extname 
            FROM pg_extension 
            WHERE extname IN ('vector', 'uuid-ossp')
            ORDER BY extname;
        """)
        extensions = [row[0] for row in cur.fetchall()]
        return extensions


def list_tables(conn):
    """Lista todas as tabelas do schema público"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        return tables


def list_views(conn):
    """Lista todas as views do schema público"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.views 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        views = [row[0] for row in cur.fetchall()]
        return views


def main():
    """Função principal"""
    print("🔍 Verificando conexão com o banco de dados...")
    print("-" * 60)
    
    # Obtém configuração
    try:
        db_config = get_db_config()
        print(f"📊 Configuração:")
        print(f"   Host: {db_config['host']}")
        print(f"   Port: {db_config['port']}")
        print(f"   Database: {db_config['database']}")
        print(f"   User: {db_config['user']}")
        print()
    except Exception as e:
        print(f"❌ Erro ao ler configuração: {e}")
        print("   Certifique-se de que o arquivo .env existe ou as variáveis de ambiente estão definidas.")
        sys.exit(1)
    
    # Tenta conectar
    try:
        conn = psycopg2.connect(**db_config)
        print("✅ Conexão estabelecida com sucesso!")
        print()
    except psycopg2.OperationalError as e:
        print(f"❌ Erro ao conectar no banco de dados:")
        print(f"   {e}")
        print()
        print("💡 Dicas:")
        print("   1. Verifique se o container está rodando: docker-compose ps")
        print("   2. Verifique se o PostgreSQL está acessível na porta configurada")
        print("   3. Verifique as credenciais no arquivo .env")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        sys.exit(1)
    
    try:
        # Verifica extensões
        extensions = check_extensions(conn)
        print(f"🔌 Extensões instaladas: {', '.join(extensions) if extensions else 'Nenhuma'}")
        expected_extensions = ['vector', 'uuid-ossp']
        missing_extensions = [ext for ext in expected_extensions if ext not in extensions]
        if missing_extensions:
            print(f"   ⚠️  Extensões faltando: {', '.join(missing_extensions)}")
        print()
        
        # Lista tabelas
        tables = list_tables(conn)
        print(f"📋 Tabelas encontradas ({len(tables)}):")
        if tables:
            for table in tables:
                print(f"   ✓ {table}")
        else:
            print("   ⚠️  Nenhuma tabela encontrada")
        print()
        
        # Lista views
        views = list_views(conn)
        if views:
            print(f"👁️  Views encontradas ({len(views)}):")
            for view in views:
                print(f"   ✓ {view}")
            print()
        
        # Verifica tabelas esperadas
        expected_tables = ['doctors', 'knowledge_base', 'consultations', 'prescriptions', 'audit_logs']
        found_tables = [t for t in expected_tables if t in tables]
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"⚠️  Tabelas esperadas não encontradas: {', '.join(missing_tables)}")
            print()
            print("💡 Execute o script de inicialização SQL manualmente se necessário.")
        else:
            print("✅ Todas as tabelas esperadas foram encontradas!")
            print()
        
        # Mensagem final de sucesso
        if found_tables:
            tables_str = ', '.join(found_tables)
            print(f"✅ Conexão OK: Tabelas [{tables_str}] encontradas")
        
    except Exception as e:
        print(f"❌ Erro ao consultar banco de dados: {e}")
        sys.exit(1)
    finally:
        conn.close()
        print("🔒 Conexão fechada.")


if __name__ == '__main__':
    main()
