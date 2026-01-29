import logging
import uvicorn
from fastapi import FastAPI, HTTPException, Depends  # <--- [NOVO] Adicionei Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# --- IMPORTAÇÃO DA SEGURANÇA (O CADEADO) ---
try:
    from auth_bearer import JWTBearer
except ImportError:
    # Fallback caso esteja rodando de uma pasta acima
    try:
        from backend.auth_bearer import JWTBearer
    except ImportError:
        raise ImportError("❌ ERRO: O arquivo 'auth_bearer.py' não foi encontrado ao lado do main.py!")

# --- IMPORTAÇÃO BLINDADA DO RAG ---
try:
    from backend.rag_service import RAGService
except ImportError:
    try:
        from rag_service import RAGService
    except ImportError:
        RAGService = None 

# --- MODELO ---
class PrescriptionRequest(BaseModel):
    symptoms: str
    diagnosis: str | None = None

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("PrescrittoMED")

app = FastAPI(title="PrescrittoMED API")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_service = None

@app.on_event("startup")
async def startup_event():
    global rag_service
    logger.info("🚀 Iniciando Servidor PrescrittoMED...")
    try:
        if RAGService:
            rag_service = RAGService()
            logger.info("✅ RAG Service conectado com sucesso.")
        else:
            logger.error("❌ ERRO CRÍTICO: Arquivo rag_service.py não encontrado.")
    except Exception as e:
        logger.error(f"❌ Erro ao instanciar IA: {e}")

# --- ROTA PRINCIPAL (AGORA PROTEGIDA 🔒) ---
@app.post("/api/v1/prescribe", dependencies=[Depends(JWTBearer())]) 
async def prescribe(request: PrescriptionRequest):
    logger.info(f"📩 Pedido recebido (Usuário Autenticado): {request.symptoms}")
    
    if not rag_service:
        raise HTTPException(status_code=503, detail="Serviço de IA offline.")

    try:
        # Chama a IA
        result = rag_service.prescribe(request.symptoms, request.diagnosis)
        logger.info(f"📤 Resposta gerada: {str(result)[:100]}...") 
        return result

    except Exception as e:
        logger.error(f"❌ Erro Interno no processamento: {e}")
        raise HTTPException(status_code=500, detail=f"Erro na IA: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)