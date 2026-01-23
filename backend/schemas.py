"""
Schemas Pydantic para a API FastAPI - SmartRx AI
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PrescriptionRequest(BaseModel):
    """Schema de entrada para o endpoint de prescrição"""
    symptoms: str = Field(..., description="Sintomas relatados pelo paciente", min_length=3)
    diagnosis: Optional[str] = Field(None, description="Diagnóstico (opcional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "symptoms": "Dor de garganta, febre e dificuldade para engolir",
                "diagnosis": "Amigdalite bacteriana"
            }
        }


class MedicationResponse(BaseModel):
    """Schema de resposta para um medicamento"""
    nome: str = Field(..., description="Nome do medicamento")
    principio_ativo: str = Field(..., description="Princípio ativo")
    forma: str = Field(..., description="Forma farmacêutica")
    concentracao: str = Field(..., description="Concentração")
    posologia: str = Field(..., description="Posologia detalhada")
    via: str = Field(..., description="Via de administração")
    frequencia: str = Field(..., description="Frequência")
    duracao: str = Field(..., description="Duração do tratamento")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")


class SourceResponse(BaseModel):
    """Schema de resposta para fonte consultada"""
    source_id: str = Field(..., description="ID da fonte")
    source_type: str = Field(..., description="Tipo da fonte")
    title: str = Field(..., description="Título da fonte")
    confidence_score: Optional[float] = Field(None, description="Score de similaridade (0-1)")


class PrescriptionResponse(BaseModel):
    """Schema de resposta completa da prescrição"""
    medicamentos: List[MedicationResponse] = Field(..., description="Lista de medicamentos prescritos")
    resumo_tecnico_medico: List[str] = Field(..., description="Resumo técnico para o médico")
    orientacoes_ao_paciente: List[str] = Field(..., description="Orientações para o paciente")
    alertas_seguranca: List[str] = Field(default_factory=list, description="Alertas de segurança")
    monitorizacao: List[str] = Field(default_factory=list, description="Itens de monitorização")
    fontes: List[SourceResponse] = Field(..., description="Fontes consultadas pela IA")
    confidence_score: Optional[float] = Field(None, description="Score de confiança geral (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "medicamentos": [
                    {
                        "nome": "Amoxicilina",
                        "principio_ativo": "Amoxicilina",
                        "forma": "Cápsula",
                        "concentracao": "500mg",
                        "posologia": "1 cápsula",
                        "via": "Oral",
                        "frequencia": "A cada 8 horas",
                        "duracao": "10 dias",
                        "observacoes": "Tomar após refeições"
                    }
                ],
                "resumo_tecnico_medico": [
                    "Tratamento de primeira linha para amigdalite bacteriana",
                    "Antibiótico de amplo espectro"
                ],
                "orientacoes_ao_paciente": [
                    "Completar o tratamento mesmo com melhora dos sintomas",
                    "Retornar se não houver melhora em 48-72h"
                ],
                "alertas_seguranca": [
                    "Não exceder a dosagem prescrita",
                    "Evitar álcool durante o tratamento"
                ],
                "monitorizacao": [
                    "Avaliar resposta ao tratamento em 48-72h"
                ],
                "fontes": [
                    {
                        "source_id": "pcdt_amigdalite_001",
                        "source_type": "OFFICIAL_PROTOCOL",
                        "title": "PCDT - Amigdalite Bacteriana",
                        "confidence_score": 0.85
                    }
                ],
                "confidence_score": 0.85
            }
        }
