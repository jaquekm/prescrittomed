"""
FastAPI Backend para SmartRx AI (PrescrittoMed)
API REST para geração de prescrições médicas com RAG
"""

import logging
from contextlib import asynccontextmanager
from typing import Dict
import uvicorn

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# --- ATENÇÃO: Estes arquivos serão criados nos próximos passos ---
# Se o VS Code marcar erro (sublinhado vermelho), é normal por enquanto!
from schemas import PrescriptionRequest, PrescriptionResponse
from rag_service import RAGService

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instância global do serviço RAG
rag_service: RAGService = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação (Inicia e Para o Robô)"""
    global rag_service
    logger.info("🚀 Iniciando SmartRx AI Backend...")
    try:
        # Aqui ele tenta conectar com a IA. Se falhar, avisamos no log.
        rag_service = RAGService()
        logger.info("✅ RAG Service inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Aviso: RAG Service não pôde ser iniciado (Verifique .env ou chaves): {e}")
        # Não vamos dar 'raise' aqui para permitir que o servidor suba mesmo sem IA por enquanto
    
    yield
    
    logger.info("🛑 Encerrando SmartRx AI Backend...")

# Cria aplicação FastAPI
app = FastAPI(
    title="PrescrittoMed AI API",
    description="API para geração de prescrições médicas assistidas por IA.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração CORS (Permite que o Frontend converse com o Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", tags=["Health"])
async def root():
    return {"message": "PrescrittoMed API está Online 🤖"}

@app.get("/health", tags=["Health"])
async def health_check():
    status_rag = "available" if rag_service else "unavailable"
    return {"status": "healthy", "rag_service": status_rag}

@app.post("/api/v1/prescribe", response_model=PrescriptionResponse, tags=["Prescription"])
async def prescribe(request: PrescriptionRequest):
    if rag_service is None:
        raise HTTPException(
            status_code=503, 
            detail="O serviço de IA não foi iniciado corretamente."
        )
    
    try:
        # A mágica acontece aqui
        prescription = rag_service.prescribe(request.symptoms, request.diagnosis)
        return prescription
    except Exception as e:
        logger.error(f"Erro ao prescrever: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Comando para rodar o servidor
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)