import os
import json
import logging
import requests
from typing import Optional
from openai import OpenAI
from decouple import config

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        # 1. Configura OpenAI
        api_key = config("OPENAI_API_KEY", default=os.getenv("OPENAI_API_KEY"))
        if not api_key:
            logger.error("❌ OPENAI_API_KEY não encontrada!")
            raise ValueError("OPENAI_API_KEY ausente")
        self.client = OpenAI(api_key=api_key)

        # 2. Configura Supabase (Modo API REST - Bypass de Instalação)
        self.sb_url = config("SUPABASE_URL", default=os.getenv("SUPABASE_URL"))
        self.sb_key = config("SUPABASE_KEY", default=os.getenv("SUPABASE_KEY"))
        
        if not self.sb_url or not self.sb_key:
            logger.warning("⚠️ Credenciais do Supabase não encontradas. O histórico não será salvo.")

    def _salvar_no_supabase(self, sintomas: str, diagnostico: Optional[str], prescricao: dict):
        """
        Envia os dados para o Supabase usando HTTP padrão (requests),
        evitando a necessidade de instalar a biblioteca pesada.
        """
        if not self.sb_url or not self.sb_key:
            return

        try:
            # Endpoint da tabela (REST API padrão do Supabase)
            # Remove barra extra se houver
            base_url = self.sb_url.rstrip('/')
            url = f"{base_url}/rest/v1/historico_prescricoes"
            
            headers = {
                "apikey": self.sb_key,
                "Authorization": f"Bearer {self.sb_key}",
                "Content-Type": "application/json",
                "Prefer": "return=minimal" # Não precisa retornar o objeto criado, economiza dados
            }
            
            payload = {
                "sintomas": sintomas,
                "diagnostico_previo": diagnostico,
                "prescricao_json": prescricao
            }

            response = requests.post(url, json=payload, headers=headers)
            
            if response.status_code in [200, 201, 204]:
                logger.info("💾 Prescrição salva no Supabase (Via API REST).")
            else:
                logger.error(f"⚠️ Falha ao salvar no Supabase: {response.status_code} - {response.text}")
                
        except Exception as e:
            logger.error(f"❌ Erro de conexão com Supabase: {e}")

    def prescribe(self, symptoms: str, diagnosis: Optional[str] = None) -> dict:
        logger.info(f"📩 Processando sintomas: {symptoms}")

        # Prompt do Sistema (Mantivemos a mesma lógica Sênior)
        system_prompt = """
        Você é o SmartRx AI, assistente médico farmacológico.
        Retorne APENAS um JSON válido seguindo estritamente esta estrutura:
        {
            "prescricoes": [
                {
                    "medicamento": {
                        "nome": "Nome do Medicamento",
                        "fonte": "Fonte da informação",
                        "url_bula": "URL opcional",
                        "nota_fixa": "Uso sob prescrição."
                    },
                    "resumo": {
                        "indicacoes_para_que_serve": ["Indicação 1"],
                        "como_usar_posologia": ["Posologia detalhada"],
                        "efeitos_colaterais": ["Efeito 1"],
                        "contraindicacoes": ["Contraindicação 1"],
                        "advertencias_e_interacoes": ["Interação 1"],
                        "orientacoes_ao_paciente": ["Orientação 1"]
                    },
                    "nota_fixa": "Consulte um médico."
                }
            ]
        }
        Se for emergência grave, retorne um JSON com orientação de ir ao PS.
        """

        user_content = f"Paciente apresenta: {symptoms}."
        if diagnosis:
            user_content += f" Diagnóstico/Suspeita: {diagnosis}."

        try:
            # Chamada OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo-0125",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            parsed_json = json.loads(content)

            # Salva no banco (Assíncrono na lógica, mas síncrono aqui por simplicidade)
            self._salvar_no_supabase(symptoms, diagnosis, parsed_json)

            return parsed_json

        except Exception as e:
            logger.error(f"❌ Erro crítico: {e}")
            return {
                "prescricoes": [{
                    "medicamento": {"nome": "Erro no Sistema", "fonte": "Backend"},
                    "resumo": {},
                    "nota_fixa": "Por favor, tente novamente."
                }]
            }