"""
Serviço de RAG (Retrieval-Augmented Generation) para SmartRx AI
Busca semântica no banco de conhecimento e geração de prescrições
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from decouple import config
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector

logger = logging.getLogger(__name__)


class RAGService:
    """Serviço para busca RAG e geração de prescrições"""
    
    def __init__(self):
        self.openai_client = OpenAI(api_key=config("OPENAI_API_KEY"))
        self.embedding_model = "text-embedding-3-small"  # 1536 dimensões
        self.llm_model = "gpt-4o"
        self.db_url = self._get_db_url()
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def _get_db_url(self) -> str:
        """Obtém URL de conexão do banco de dados"""
        database_url = os.getenv('DATABASE_URL')
        
        if database_url:
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
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding vetorial para um texto usando OpenAI
        
        Args:
            text: Texto para gerar embedding
        
        Returns:
            Lista de floats representando o vetor de embedding
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    def search_knowledge_base(
        self, 
        query_embedding: List[float], 
        limit: int = 5,
        min_similarity: float = 0.7
    ) -> List[Dict]:
        """
        Busca no banco de conhecimento usando similaridade de cosseno
        
        Args:
            query_embedding: Vetor de embedding da query
            limit: Número máximo de resultados
            min_similarity: Similaridade mínima (0-1)
        
        Returns:
            Lista de dicionários com resultados da busca
        """
        session = self.Session()
        try:
            # Converte lista para formato aceito pelo pgvector
            # pgvector aceita arrays PostgreSQL ou strings no formato '[1,2,3]'
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            # Query de busca por similaridade de cosseno
            # <=> é o operador de distância de cosseno no pgvector
            # 1 - distância = similaridade (quanto menor a distância, maior a similaridade)
            # Usamos bindparam para passar o vetor corretamente
            from sqlalchemy import bindparam
            
            query = text("""
                SELECT 
                    id,
                    content,
                    source_type,
                    source_title,
                    source_id,
                    version_date,
                    metadata,
                    1 - (embedding <=> CAST(:embedding_vec AS vector)) AS similarity
                FROM knowledge_base
                WHERE 
                    validity_status = 'ACTIVE'
                    AND embedding IS NOT NULL
                    AND (1 - (embedding <=> CAST(:embedding_vec AS vector))) >= :min_sim
                ORDER BY embedding <=> CAST(:embedding_vec AS vector)
                LIMIT :limit
            """).bindparams(
                bindparam('embedding_vec', embedding_str),
                bindparam('min_sim', min_similarity),
                bindparam('limit', limit)
            )
            
            result = session.execute(query)
            
            results = []
            for row in result:
                results.append({
                    'id': str(row.id),
                    'content': row.content,
                    'source_type': row.source_type,
                    'source_title': row.source_title,
                    'source_id': row.source_id or '',
                    'version_date': row.version_date.isoformat() if row.version_date else None,
                    'metadata': row.metadata or {},
                    'similarity': float(row.similarity)
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Erro ao buscar no knowledge base: {e}")
            raise
        finally:
            session.close()
    
    def generate_prescription(
        self, 
        symptoms: str, 
        diagnosis: Optional[str],
        context_docs: List[Dict]
    ) -> Dict:
        """
        Gera prescrição usando GPT-4o com contexto RAG
        
        Args:
            symptoms: Sintomas do paciente
            diagnosis: Diagnóstico (opcional)
            context_docs: Documentos relevantes do knowledge base
        
        Returns:
            Dicionário com a prescrição estruturada
        """
        # Constrói contexto a partir dos documentos encontrados
        context_text = "\n\n".join([
            f"[Fonte: {doc['source_title']} ({doc['source_type']})]\n{doc['content']}"
            for doc in context_docs
        ])
        
        # Prompt do sistema
        system_prompt = """Você é um assistente médico especializado em gerar prescrições baseadas em protocolos clínicos oficiais.

IMPORTANTE:
- Você é uma ferramenta de APOIO à decisão. O médico é sempre o responsável final.
- Baseie-se APENAS nas fontes fornecidas no contexto.
- Se não houver informação suficiente no contexto, indique isso claramente.
- Sempre cite as fontes usadas.
- Siga a estrutura JSON fornecida.

Retorne APENAS JSON válido, sem markdown ou texto adicional."""

        # Prompt do usuário
        user_prompt = f"""Com base nos sintomas e diagnóstico abaixo, e usando APENAS as informações do contexto fornecido, gere uma prescrição médica estruturada.

SINTOMAS: {symptoms}
DIAGNÓSTICO: {diagnosis or 'Não especificado'}

CONTEXTO (Fontes Consultadas):
{context_text}

Retorne um JSON com a seguinte estrutura:
{{
    "medicamentos": [
        {{
            "nome": "Nome comercial",
            "principio_ativo": "Princípio ativo",
            "forma": "Forma farmacêutica",
            "concentracao": "Concentração",
            "posologia": "Posologia detalhada",
            "via": "Via de administração",
            "frequencia": "Frequência",
            "duracao": "Duração",
            "observacoes": "Observações (opcional)"
        }}
    ],
    "resumo_tecnico_medico": ["ponto 1", "ponto 2"],
    "orientacoes_ao_paciente": ["orientação 1", "orientação 2"],
    "alertas_seguranca": ["alerta 1", "alerta 2"],
    "monitorizacao": ["item 1", "item 2"]
}}"""

        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,  # Determinístico conforme requisitos
                response_format={"type": "json_object"}  # Força resposta JSON
            )
            
            import json
            prescription_json = json.loads(response.choices[0].message.content)
            
            # Adiciona informações das fontes
            prescription_json['fontes'] = [
                {
                    'source_id': doc['source_id'],
                    'source_type': doc['source_type'],
                    'title': doc['source_title'],
                    'confidence_score': doc['similarity']
                }
                for doc in context_docs
            ]
            
            # Calcula confidence score médio
            if context_docs:
                prescription_json['confidence_score'] = sum(
                    doc['similarity'] for doc in context_docs
                ) / len(context_docs)
            else:
                prescription_json['confidence_score'] = 0.0
            
            return prescription_json
            
        except Exception as e:
            logger.error(f"Erro ao gerar prescrição: {e}")
            raise
    
    def prescribe(
        self, 
        symptoms: str, 
        diagnosis: Optional[str] = None
    ) -> Dict:
        """
        Método principal: busca RAG + geração de prescrição
        
        Args:
            symptoms: Sintomas do paciente
            diagnosis: Diagnóstico (opcional)
        
        Returns:
            Dicionário com prescrição completa
        """
        # 1. Gera embedding da query
        query_text = f"{symptoms} {diagnosis or ''}".strip()
        query_embedding = self.generate_embedding(query_text)
        
        # 2. Busca no knowledge base
        context_docs = self.search_knowledge_base(query_embedding, limit=5, min_similarity=0.7)
        
        # 3. Se não encontrou documentos suficientes, retorna erro
        if not context_docs:
            raise ValueError(
                "Não foram encontrados protocolos clínicos suficientes para gerar a prescrição. "
                "Sistema em modo manual."
            )
        
        # 4. Gera prescrição com contexto
        prescription = self.generate_prescription(symptoms, diagnosis, context_docs)
        
        return prescription
