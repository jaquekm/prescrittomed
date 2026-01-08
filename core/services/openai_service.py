import logging

from decouple import config
from openai import OpenAI


logger = logging.getLogger(__name__)


class OpenAIServiceError(Exception):
    pass


def generate_chat_completion(prompt_sistema, prompt_usuario, model="gpt-4o-mini"):
    try:
        client = OpenAI(api_key=config("OPENAI_API_KEY"))
        resposta = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario},
            ],
        )
        return resposta.choices[0].message.content
    except Exception:
        logger.exception("Falha ao chamar OpenAI.")
        raise OpenAIServiceError("Falha ao gerar resposta de IA. Tente novamente mais tarde.")


def testar_conexao():
    prompt_sistema = "Você é um assistente médico útil."
    prompt_usuario = "Diga: 'Olá! O Agente Prescritto está conectado e pronto para ajudar.'"
    return generate_chat_completion(prompt_sistema, prompt_usuario)
