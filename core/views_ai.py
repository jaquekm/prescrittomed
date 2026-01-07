import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .permissions import role_required
from .services.openai_service import OpenAIServiceError, testar_conexao


logger = logging.getLogger(__name__)


@login_required(login_url="/login/")
@role_required("ADMIN")
def teste_openai(request):
    try:
        texto = testar_conexao()
        return JsonResponse({"status": "ok", "mensagem": texto})
    except OpenAIServiceError:
        return JsonResponse(
            {"status": "error", "mensagem": "Serviço de IA indisponível no momento."},
            status=503,
        )
    except Exception:
        logger.exception("Erro inesperado ao testar OpenAI.")
        return JsonResponse(
            {"status": "error", "mensagem": "Erro inesperado ao processar a solicitação."},
            status=500,
        )
