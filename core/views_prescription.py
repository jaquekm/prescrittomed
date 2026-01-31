from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from typing import List
import json
import io
import textwrap
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from auth_bearer import JWTBearer
from openai_prescription import generate_prescription_rag 

router = APIRouter()

# --- MODELOS DE DADOS (Corrigindo o erro 422) ---
class PatientData(BaseModel):
    anamnese: str  # O frontend precisa enviar com este nome exato
    hipotese: str = ""

class MedicamentoPDF(BaseModel):
    nome: str
    posologia: str
    aviso: str = ""

class ReceitaRequest(BaseModel):
    paciente_nome: str = "Paciente"
    medicamentos: List[MedicamentoPDF]

# --- ROTA 1: APENAS MOSTRAR DADOS NA TELA ---
@router.post("/api/v1/prescribe", dependencies=[Depends(JWTBearer())])
async def consult_ai(data: PatientData):
    try:
        # Gera o texto da IA
        ai_response_text = generate_prescription_rag(data.anamnese, data.hipotese)
        
        # Garante que é um JSON limpo
        ai_response_text = ai_response_text.replace("```json", "").replace("```", "")
        receita_data = json.loads(ai_response_text)
        
        return receita_data 

    except Exception as e:
        print(f"Erro na IA: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ROTA 2: GERAR O PDF FINAL (Com os dados que você conferiu) ---
@router.post("/api/v1/generate-pdf", dependencies=[Depends(JWTBearer())])
async def create_pdf(data: ReceitaRequest):
    try:
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        largura, altura = A4
        
        # Cabeçalho
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, altura - 50, "PrescrittoMED")
        p.line(50, altura - 60, largura - 50, altura - 60)
        
        y = altura - 100
        
        for med in data.medicamentos:
            # Nome do Medicamento
            p.setFont("Helvetica-Bold", 14)
            p.setFillColor(colors.darkblue)
            p.drawString(50, y, f"• {med.nome}")
            y -= 20
            
            # Posologia
            p.setFont("Helvetica", 12)
            p.setFillColor(colors.black)
            lines = textwrap.wrap(f"Uso: {med.posologia}", width=80)
            for line in lines:
                p.drawString(70, y, line)
                y -= 15
                
            # Aviso
            if med.aviso:
                p.setFont("Helvetica-Oblique", 10)
                p.setFillColor(colors.red)
                p.drawString(70, y, f"Obs: {med.aviso}")
                y -= 15
            
            y -= 15 # Espaço entre itens
            
        p.save()
        buffer.seek(0)
        return Response(content=buffer.getvalue(), media_type="application/pdf")

    except Exception as e:
        print(f"Erro PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))