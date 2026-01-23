#!/usr/bin/env python3
"""
Script para popular o banco de dados com dados iniciais (seed data).
Insere medicamentos e protocolos na tabela knowledge_base para testes.
"""

import os
import sys
import random
from datetime import date
from pathlib import Path
from typing import List

# Adiciona o diretório raiz ao path para importar decouple
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from decouple import config
    from sqlalchemy import create_engine, text, Column, String, Text, Date, Integer, JSON
    from sqlalchemy.dialects.postgresql import UUID, JSONB
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from pgvector.sqlalchemy import Vector
except ImportError as e:
    print(f"❌ Erro: Dependências não instaladas.")
    print(f"   Execute: pip install sqlalchemy pgvector python-decouple psycopg2-binary")
    print(f"   Detalhes: {e}")
    sys.exit(1)


# Base para modelos SQLAlchemy
Base = declarative_base()


class KnowledgeBase(Base):
    """Modelo SQLAlchemy para a tabela knowledge_base"""
    __tablename__ = 'knowledge_base'
    
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text('uuid_generate_v4()'))
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)
    source_type = Column(String(50), nullable=False)
    source_title = Column(String(255), nullable=False)
    source_id = Column(String(255), nullable=True)
    version_date = Column(Date, nullable=True)
    validity_status = Column(String(20), default='ACTIVE')
    metadata = Column(JSONB, nullable=True)
    hospital_id = Column(Integer, nullable=True)
    created_at = Column('created_at', nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column('updated_at', nullable=False, server_default=text('CURRENT_TIMESTAMP'))


def get_db_url():
    """Obtém URL de conexão do banco de dados das variáveis de ambiente"""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Garante que a URL está no formato correto para SQLAlchemy
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # Fallback: constrói URL a partir de variáveis individuais
    host = config('POSTGRES_HOST', default='localhost')
    port = config('POSTGRES_PORT', default=5432, cast=int)
    database = config('POSTGRES_DB', default='prescrittomed_db')
    user = config('POSTGRES_USER', default='prescrittomed')
    password = config('POSTGRES_PASSWORD', default='prescrittomed_pass')
    
    return f"postgresql://{user}:{password}@{host}:{port}/{database}"


def generate_fake_embedding(dimension: int = 1536) -> List[float]:
    """
    Gera um vetor de embedding fake (aleatório) para testes.
    
    Args:
        dimension: Dimensão do vetor (padrão: 1536 para OpenAI text-embedding-3-small)
    
    Returns:
        Lista de floats representando o vetor de embedding
    """
    # Gera valores aleatórios normalizados entre -1 e 1
    # Isso simula um embedding real que geralmente tem valores nesse range
    return [random.uniform(-1.0, 1.0) for _ in range(dimension)]


def get_seed_data():
    """
    Retorna os dados iniciais para popular a knowledge_base.
    
    Returns:
        Lista de dicionários com os dados de seed
    """
    return [
        {
            'content': (
                'Amoxicilina 500mg - Antibiótico de amplo espectro da classe das penicilinas. '
                'Indicado para tratamento de infecções bacterianas do trato respiratório, '
                'infecções do trato urinário, infecções de pele e tecidos moles. '
                'Posologia: Adultos: 500mg a cada 8 horas por 7-10 dias. '
                'Crianças: 25-50mg/kg/dia dividido em 3 doses. '
                'Contraindicações: Hipersensibilidade a penicilinas. '
                'Efeitos adversos: Diarreia, náusea, erupções cutâneas. '
                'Interações: Pode reduzir eficácia de anticoncepcionais orais.'
            ),
            'source_type': 'DRUG_LEAFLET',
            'source_title': 'Bula - Amoxicilina 500mg',
            'source_id': 'bula_amoxicilina_500mg_001',
            'version_date': date(2024, 1, 15),
            'validity_status': 'ACTIVE',
            'metadata': {
                'tier': 3,
                'medication_name': 'Amoxicilina',
                'dosage': '500mg',
                'pregnancy_category': 'B',
                'is_pediatric': True,
                'is_adult': True
            }
        },
        {
            'content': (
                'Protocolo Clínico e Diretrizes Terapêuticas (PCDT) - Amigdalite Bacteriana. '
                'Ministério da Saúde - Portaria SAS/MS nº 1.238/2014. '
                'Diagnóstico: Clínico baseado em sinais e sintomas (dor de garganta, febre, '
                'adenomegalia cervical, exsudato purulento). Teste rápido de estreptococo quando disponível. '
                'Tratamento de primeira linha: Amoxicilina 500mg a cada 8 horas por 10 dias. '
                'Alternativa em caso de alergia à penicilina: Azitromicina 500mg 1x/dia por 5 dias. '
                'Critérios de melhora: Redução da febre e dor em 48-72h. '
                'Critérios de encaminhamento: Falha terapêutica, complicações, recidivas frequentes.'
            ),
            'source_type': 'OFFICIAL_PROTOCOL',
            'source_title': 'PCDT - Amigdalite Bacteriana',
            'source_id': 'pcdt_amigdalite_001',
            'version_date': date(2024, 3, 1),
            'validity_status': 'ACTIVE',
            'metadata': {
                'tier': 1,
                'protocol_number': 'SAS/MS 1238/2014',
                'condition': 'Amigdalite Bacteriana',
                'is_pediatric': True,
                'is_adult': True
            }
        },
        {
            'content': (
                'Dipirona 1g - Analgésico e antitérmico. Indicado para tratamento de dor '
                'de intensidade moderada a intensa e febre. Posologia: Adultos: 1g a cada 6-8 horas, '
                'máximo 4g/dia. Crianças acima de 3 meses: 10-15mg/kg a cada 6-8 horas. '
                'Contraindicações: Hipersensibilidade ao fármaco, porfiria, insuficiência hepática grave, '
                'insuficiência renal grave, asma induzida por AINEs, gravidez (3º trimestre). '
                'Efeitos adversos: Reações cutâneas, agranulocitose (raro), hipotensão. '
                'Precauções: Uso em gestantes (1º e 2º trimestre apenas se benefício supera risco), '
                'lactantes, pacientes com histórico de alergia a AINEs.'
            ),
            'source_type': 'DRUG_LEAFLET',
            'source_title': 'Bula - Dipirona 1g',
            'source_id': 'bula_dipirona_1g_001',
            'version_date': date(2024, 2, 10),
            'validity_status': 'ACTIVE',
            'metadata': {
                'tier': 3,
                'medication_name': 'Dipirona',
                'dosage': '1g',
                'pregnancy_category': 'D',
                'is_pediatric': True,
                'is_adult': True,
                'warning_pregnancy': True
            }
        }
    ]


def seed_database():
    """Função principal para popular o banco de dados"""
    print("🌱 Iniciando seed do banco de dados...")
    print("-" * 60)
    
    # Obtém URL de conexão
    try:
        db_url = get_db_url()
        print(f"📊 Conectando ao banco de dados...")
        print(f"   Host: {db_url.split('@')[1].split('/')[0] if '@' in db_url else 'N/A'}")
    except Exception as e:
        print(f"❌ Erro ao obter configuração do banco: {e}")
        print("   Certifique-se de que o arquivo .env existe ou as variáveis de ambiente estão definidas.")
        sys.exit(1)
    
    # Cria engine e sessão
    try:
        engine = create_engine(db_url, echo=False)
        
        # Testa conexão
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            print(f"✅ Conectado ao PostgreSQL")
            print(f"   Versão: {version.split(',')[0]}")
            print()
    except Exception as e:
        print(f"❌ Erro ao conectar no banco de dados:")
        print(f"   {e}")
        print()
        print("💡 Dicas:")
        print("   1. Verifique se o container Docker está rodando: docker-compose ps")
        print("   2. Verifique as credenciais no arquivo .env")
        print("   3. Teste a conexão: python check_db.py")
        sys.exit(1)
    
    # Cria sessão
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Verifica se a tabela existe
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'knowledge_base'
                )
            """))
            table_exists = result.fetchone()[0]
            
            if not table_exists:
                print("❌ Tabela 'knowledge_base' não encontrada!")
                print("   Execute o script de inicialização SQL primeiro:")
                print("   docker-compose up -d")
                sys.exit(1)
        
        # Obtém dados de seed
        seed_items = get_seed_data()
        
        print(f"📝 Preparando {len(seed_items)} itens para inserção...")
        print()
        
        inserted_count = 0
        
        for item_data in seed_items:
            # Gera embedding fake
            embedding_vector = generate_fake_embedding(1536)
            
            # Cria objeto KnowledgeBase
            kb_item = KnowledgeBase(
                content=item_data['content'],
                embedding=embedding_vector,  # pgvector converterá automaticamente
                source_type=item_data['source_type'],
                source_title=item_data['source_title'],
                source_id=item_data['source_id'],
                version_date=item_data['version_date'],
                validity_status=item_data['validity_status'],
                metadata=item_data['metadata']
            )
            
            # Adiciona à sessão
            session.add(kb_item)
            print(f"   ✓ {item_data['source_title']} ({item_data['source_type']})")
        
        # Commit das inserções
        session.commit()
        inserted_count = len(seed_items)
        
        print()
        print(f"✅ {inserted_count} itens inseridos com sucesso!")
        print()
        
        # Verifica inserção
        count = session.query(KnowledgeBase).count()
        print(f"📊 Total de itens na knowledge_base: {count}")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Erro ao inserir dados: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()
        engine.dispose()
        print("🔒 Conexão fechada.")


if __name__ == '__main__':
    seed_database()
