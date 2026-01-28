import json
import logging
import re

from decouple import config
from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenAIPrescriptionError(Exception):
    pass


PII_KEYS = {"nome", "nome_completo", "cpf", "rg", "email", "telefone", "endereco", "data_nascimento"}
REQUIRED_MEDICATION_FIELDS = {
    "nome",
    "principio_ativo",
    "forma",
    "concentracao",
    "posologia",
    "via",
    "frequencia",
    "duracao",
}


def _redact_text(value):
    if not isinstance(value, str):
        return value
    value = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "[CPF_REMOVIDO]", value)
    value = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[EMAIL_REMOVIDO]", value)
    value = re.sub(r"\b\+?\d{2}\s?\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b", "[TEL_REMOVIDO]", value)
    return value


def sanitize_context(contexto_clinico):
    sanitized = {}
    for key, value in (contexto_clinico or {}).items():
        if key in PII_KEYS:
            continue
        sanitized[key] = _redact_text(value)
    return sanitized


def validate_prescription_payload(payload):
    if not isinstance(payload, dict):
        return False
    required_keys = {
        "resumo_tecnico_medico",
        "orientacoes_ao_paciente",
        "medicamentos",
        "alertas_seguranca",
        "monitorizacao",
        "fontes",
    }
    if not required_keys.issubset(payload.keys()):
        return False
    if not isinstance(payload["medicamentos"], list):
        return False
    for item in payload["medicamentos"]:
        if not isinstance(item, dict):
            return False
        if not REQUIRED_MEDICATION_FIELDS.issubset(item.keys()):
            return False
    if not isinstance(payload["orientacoes_ao_paciente"], list):
        return False
    if not isinstance(payload["alertas_seguranca"], list):
        return False
    if not isinstance(payload["monitorizacao"], list):
        return False
    if not isinstance(payload["fontes"], list):
        return False
    return True


def generate_prescription(contexto_clinico):
    sanitized = sanitize_context(contexto_clinico or {})
    
    # Schema definido (mesmo do seu código)
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "resumo_tecnico_medico": {"type": "array", "items": {"type": "string"}},
            "orientacoes_ao_paciente": {"type": "array", "items": {"type": "string"}},
            "medicamentos": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "nome": {"type": "string"},
                        "principio_ativo": {"type": "string"},
                        "forma": {"type": "string"},
                        "concentracao": {"type": "string"},
                        "posologia": {"type": "string"},
                        "via": {"type": "string"},
                        "frequencia": {"type": "string"},
                        "duracao": {"type": "string"},
                        "ajustes": {"type": "string"},
                        "observacoes": {"type": "string"},
                    },
                    "required": list(REQUIRED_MEDICATION_FIELDS),
                },
            },
            "alertas_seguranca": {"type": "array", "items": {"type": "string"}},
            "monitorizacao": {"type": "array", "items": {"type": "string"}},
            "fontes": {"type": "array", "items": {"type": "string"}},
        },
        "required": [
            "resumo_tecnico_medico",
            "orientacoes_ao_paciente",
            "medicamentos",
            "alertas_seguranca",
            "monitorizacao",
            "fontes",
        ],
    }

    prompt_sistema = (
        "Você gera um rascunho estruturado de prescrição. "
        "Retorne somente JSON válido conforme o schema. Não inclua PII."
    )
    prompt_usuario = json.dumps(sanitized, ensure_ascii=False)

    try:
        client = OpenAI(api_key=config("OPENAI_API_KEY"))
        
        # --- CORREÇÃO AQUI ---
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            # Mudei de 'input' para 'messages'
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
            # Ajustei o formato do json_schema para o padrão correto
            response_format={
                "type": "json_schema", 
                "json_schema": {
                    "name": "prescricao_medica",
                    "schema": schema,
                    "strict": True
                }
            },
        )
        
        # --- E CORREÇÃO AQUI NA LEITURA DA RESPOSTA ---
        # Antes estava response.output_text (incorreto)
        conteudo_json = response.choices[0].message.content
        payload = json.loads(conteudo_json)

        if not validate_prescription_payload(payload):
            raise OpenAIPrescriptionError("Resposta da IA inválida. Tente novamente.")
        return payload

    except Exception as e:
        # Adicionei o erro 'e' no log para sabermos o que aconteceu se falhar de novo
        logger.exception(f"Falha ao gerar rascunho de prescrição: {e}")
        raise OpenAIPrescriptionError(
            "Falha ao gerar rascunho de prescrição. Tente novamente mais tarde."
        )