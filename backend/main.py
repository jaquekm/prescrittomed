import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from backend.rag_service import RAGService

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PrescrittoMED API")

# Configuração de CORS (Permitir que o Frontend acesse o Backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique a URL do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NOVAS ESTRUTURAS DE DADOS (Baseadas no seu JSON) ---

class MedicamentoInfo(BaseModel):
    nome: str
    fonte: str
    url_bula: Optional[str] = None
    url_pdf: Optional[str] = None
    atualizado_em: Optional[str] = None
    observacao_fonte: Optional[str] = None

class ResumoInfo(BaseModel):
    indicacoes_para_que_serve: List[str]
    como_usar_posologia: List[str]
    efeitos_colaterais: List[str]
    contraindicacoes: List[str]
    advertencias_e_interacoes: List[str]
    orientacoes_ao_paciente: List[str]

class PrescricaoItem(BaseModel):
    medicamento: MedicamentoInfo
    resumo: ResumoInfo
    nota_fixa: str

class PrescriptionResponse(BaseModel):
    prescricoes: List[PrescricaoItem]

class PrescriptionRequest(BaseModel):
    symptoms: str
    diagnosis: Optional[str] = None

# --------------------------------------------------------

# Inicializa o Serviço de IA
rag_service = RAGService()

@app.on_event("startup")
async def startup_event():
    logger.info("🚀 Iniciando PrescrittoMED Backend...")
    try:
        # Apenas um teste rápido de conexão
        rag_service.generate_embedding("teste")
        logger.info("✅ RAG Service inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar RAG Service: {e}")

@app.get("/")
async def root():
    return {"message": "PrescrittoMED API is running"}

@app.post("/api/v1/prescribe", response_model=PrescriptionResponse)
async def prescribe(request: PrescriptionRequest):
    logger.info(f"📩 Recebendo pedido: {request.symptoms}")
    try:
        # Chama a IA
        result = rag_service.prescribe(request.symptoms, request.diagnosis)
        return result
    except Exception as e:
        logger.error(f"❌ Erro no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)