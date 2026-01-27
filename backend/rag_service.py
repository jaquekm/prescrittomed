import os
import logging
from typing import List, Dict, Optional
from decouple import config
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
import json

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        api_key = config('OPENAI_API_KEY', default=None)
        self.openai_client = OpenAI(api_key=api_key)
        self.embedding_model = "text-embedding-3-small"
        self.llm_model = "gpt-4o"
        self.db_url = self._get_db_url()
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def _get_db_url(self) -> str:
        database_url = os.getenv('DATABASE_URL')
        if database_url:
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            return database_url
        host = config('POSTGRES_HOST', default='localhost')
        port = config('POSTGRES_PORT', default=5432, cast=int)
        database = config('POSTGRES_DB', default='prescrittomed_db')
        user = config('POSTGRES_USER', default='prescrittomed')
        password = config('POSTGRES_PASSWORD', default='prescrittomed_pass')
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def generate_embedding(self, text: str) -> List[float]:
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model, input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            raise
    
    def search_knowledge_base(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        session = self.Session()
        try:
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            from sqlalchemy import bindparam
            
            # Aceita qualquer similaridade > 0.01 (quase tudo)
            query = text("""
                SELECT id, content, source_type, source_title, 
                    1 - (embedding <=> CAST(:embedding_vec AS vector)) AS similarity
                FROM knowledge_base
                WHERE validity_status = 'ACTIVE' 
                ORDER BY similarity DESC
                LIMIT :limit
            """).bindparams(
                bindparam('embedding_vec', embedding_str),
                bindparam('limit', limit)
            )
            
            result = session.execute(query)
            return [{
                'content': row.content, 
                'source_title': row.source_title, 
                'similarity': float(row.similarity)
            } for row in result]
        finally:
            session.close()
    
    def generate_prescription(self, symptoms: str, diagnosis: Optional[str], context_docs: List[Dict]) -> Dict:
        # Monta o contexto lido do banco
        context_text = "\n---\n".join([f"FONTE: {d['source_title']}\nCONTEÚDO: {d['content']}" for d in context_docs])
        
        system_prompt = """
        Você é um assistente médico do sistema PrescrittoMED.
        Sua tarefa é gerar uma lista de prescrições baseada ESTRITAMENTE no contexto fornecido.
        
        FORMATO DE SAÍDA OBRIGATÓRIO (JSON):
        O retorno deve ser um objeto JSON contendo uma lista na chave "prescricoes".
        Cada item da lista deve seguir EXATAMENTE esta estrutura:
        
        {
          "medicamento": {
            "nome": "Nome do remédio",
            "fonte": "Fonte extraída do texto",
            "url_bula": "URL se houver no texto, senão null",
            "url_pdf": null,
            "atualizado_em": "Data de hoje (AAAA-MM-DD)",
            "observacao_fonte": "Resumo sobre a fonte"
          },
          "resumo": {
            "indicacoes_para_que_serve": ["Texto 1", "Texto 2"],
            "como_usar_posologia": ["Dose adulta...", "Dose pediátrica..."],
            "efeitos_colaterais": ["Efeito 1", "Efeito 2"],
            "contraindicacoes": ["Contra 1", "Contra 2"],
            "advertencias_e_interacoes": ["Adv 1"],
            "orientacoes_ao_paciente": ["Orientação 1"]
          },
          "nota_fixa": "Este resumo não substitui a leitura integral da bula nem a orientação do profissional de saúde."
        }
        """

        user_prompt = f"""
        PACIENTE COM: {symptoms}. 
        DIAGNÓSTICO (se houver): {diagnosis}.
        
        BASE DE CONHECIMENTO (Use apenas isso):
        {context_text}
        
        Gere o JSON com as prescrições indicadas para esse caso.
        """

        try:
            response = self.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0,
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Erro GPT: {e}")
            raise
    
    def prescribe(self, symptoms: str, diagnosis: Optional[str] = None) -> Dict:
        query_text = f"{symptoms} {diagnosis or ''}".strip()
        query_embedding = self.generate_embedding(query_text)
        
        # Busca no banco
        context_docs = self.search_knowledge_base(query_embedding, limit=4)
        
        if not context_docs:
            # Fallback se banco vazio (apenas para não quebrar)
            context_docs = [{
                'source_title': 'Sistema',
                'content': 'Nenhum protocolo encontrado. Use conhecimento padrão.',
                'similarity': 0.0
            }]
        
        return self.generate_prescription(symptoms, diagnosis, context_docs)