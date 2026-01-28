import os
import logging
import json
from typing import List, Dict, Optional
from decouple import config
from openai import OpenAI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pgvector.sqlalchemy import Vector
from dotenv import load_dotenv, find_dotenv

# --- CARREGAMENTO BLINDADO ---
env_path = find_dotenv()
load_dotenv(env_path)

logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        print("--- INICIANDO RAG SERVICE ---")
        
        # 1. Tenta pegar a chave
        api_key = os.getenv("OPENAI_API_KEY") or config('OPENAI_API_KEY', default=None)

        if not api_key:
            print("❌ ERRO CRÍTICO: Chave não encontrada!")
            self.openai_client = None
        else:
            masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 10 else "Key Curta"
            print(f"✅ API Key Carregada: {masked_key}")
            self.openai_client = OpenAI(api_key=api_key)

        self.embedding_model = "text-embedding-3-small"
        self.llm_model = "gpt-4o"
        
        self.db_url = self._get_db_url()
        self.engine = create_engine(self.db_url, echo=False)
        self.Session = sessionmaker(bind=self.engine)
    
    def _get_db_url(self) -> str:
        database_url = os.getenv('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            return database_url.replace('postgres://', 'postgresql://', 1)
            
        host = config('POSTGRES_HOST', default='localhost')
        port = config('POSTGRES_PORT', default=5432, cast=int)
        database = config('POSTGRES_DB', default='prescrittomed_db')
        user = config('POSTGRES_USER', default='prescrittomed')
        password = config('POSTGRES_PASSWORD', default='prescrittomed_pass')
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def generate_embedding(self, text: str) -> List[float]:
        if not self.openai_client: raise ValueError("Sem API Key")
        try:
            return self.openai_client.embeddings.create(
                model=self.embedding_model, input=text.replace("\n", " ")
            ).data[0].embedding
        except Exception as e:
            logger.error(f"Erro Embedding: {e}")
            raise
    
    def search_knowledge_base(self, query_embedding: List[float], limit: int = 5) -> List[Dict]:
        session = self.Session()
        try:
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            # Nota: Ajuste a query conforme a estrutura real da sua tabela (se tiver source_id, uuid, etc)
            query = text("""
                SELECT id, content, source_type, source_title, 
                    1 - (embedding <=> CAST(:embedding_vec AS vector)) AS similarity
                FROM knowledge_base
                WHERE validity_status = 'ACTIVE' 
                ORDER BY similarity DESC
                LIMIT :limit
            """).bindparams(embedding_vec=embedding_str, limit=limit)
            
            result = session.execute(query)
            return [{
                'source_id': str(row.id), # Convertendo para string para garantir compatibilidade
                'content': row.content, 
                'source_type': row.source_type,
                'source_title': row.source_title, 
                'similarity': float(row.similarity)
            } for row in result]
        except Exception as e:
            print(f"⚠️ Erro busca DB: {e}")
            return []
        finally:
            session.close()
    
    def generate_prescription(self, symptoms: str, diagnosis: Optional[str], context_docs: List[Dict]) -> Dict:
        if not self.openai_client: raise ValueError("Sem API Key")

        # Prepara contexto
        if not context_docs:
            context_text = "Nenhuma informação específica encontrada na base."
        else:
            context_text = "\n---\n".join([f"FONTE ({d['source_title']}): {d['content']}" for d in context_docs])
        
        # PROMPT ALINHADO AO SCHEMA PYDANTIC
        system_prompt = """
        Você é um médico assistente do PrescrittoMED.
        Gere um JSON estritamente compatível com a seguinte estrutura.
        
        IMPORTANTE: Responda APENAS o JSON, sem markdown.
        
        Estrutura esperada (exemplo):
        {
          "medicamentos": [
            {
              "nome": "Nome",
              "principio_ativo": "Ativo",
              "forma": "Comprimido",
              "concentracao": "500mg",
              "posologia": "1 cp a cada 8h",
              "via": "Oral",
              "frequencia": "8/8h",
              "duracao": "7 dias",
              "observacoes": "Após refeições"
            }
          ],
          "resumo_tecnico_medico": ["Texto 1", "Texto 2"],
          "orientacoes_ao_paciente": ["Orientação 1"],
          "alertas_seguranca": ["Alerta 1"],
          "monitorizacao": ["Monitorar X"]
        }
        """

        user_prompt = f"PACIENTE: {symptoms}. DIAGNÓSTICO: {diagnosis}.\nCONTEXTO TÉCNICO:\n{context_text}"

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
            
            # Parse do JSON gerado pelo GPT
            generated_data = json.loads(response.choices[0].message.content)
            
            # Injeta as fontes recuperadas (para bater com o Schema SourceResponse)
            # O GPT gera o texto, nós garantimos a rastreabilidade das fontes aqui
            fontes_estruturadas = []
            for doc in context_docs:
                fontes_estruturadas.append({
                    "source_id": str(doc.get('source_id', 'unknown')),
                    "source_type": doc.get('source_type', 'REFERENCE'),
                    "title": doc.get('source_title', 'Sem título'),
                    "confidence_score": doc.get('similarity', 0.0)
                })
            
            # Adiciona metadados finais
            generated_data['fontes'] = fontes_estruturadas
            generated_data['confidence_score'] = max([f['confidence_score'] for f in fontes_estruturadas]) if fontes_estruturadas else 0.0
            
            return generated_data

        except Exception as e:
            logger.error(f"Erro GPT: {e}")
            # Retorna estrutura vazia/erro segura em caso de falha grave
            return {
                "medicamentos": [],
                "resumo_tecnico_medico": ["Erro ao gerar prescrição."],
                "orientacoes_ao_paciente": ["Consulte o suporte."],
                "alertas_seguranca": [],
                "monitorizacao": [],
                "fontes": [],
                "confidence_score": 0.0
            }
    
    def prescribe(self, symptoms: str, diagnosis: Optional[str] = None) -> Dict:
        query_text = f"{symptoms} {diagnosis or ''}".strip()
        try:
            query_embedding = self.generate_embedding(query_text)
            context_docs = self.search_knowledge_base(query_embedding, limit=4)
        except Exception as e:
            print(f"⚠️ Erro contexto: {e}")
            context_docs = []
        
        return self.generate_prescription(symptoms, diagnosis, context_docs)