"""
Schemas Pydantic para validação de dados - SmartRx AI
Seguindo ANVISA RDC 657/2022 e padrões de compliance
"""

from datetime import date, datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ActionType(str, Enum):
    """Tipos de ações registradas no audit trail"""
    INPUT_RECEIVED = "INPUT_RECEIVED"
    AI_SUGGESTION_GENERATED = "AI_SUGGESTION_GENERATED"
    DOCTOR_EDIT = "DOCTOR_EDIT"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    PRESCRIPTION_FINALIZED = "PRESCRIPTION_FINALIZED"
    PDF_GENERATED = "PDF_GENERATED"
    BREAK_GLASS_CONFIRMATION = "BREAK_GLASS_CONFIRMATION"


class MedicationSchema(BaseModel):
    """Schema para um medicamento individual"""
    nome: str = Field(..., description="Nome comercial do medicamento")
    principio_ativo: str = Field(..., description="Princípio ativo")
    forma: str = Field(..., description="Forma farmacêutica (comprimido, cápsula, etc.)")
    concentracao: str = Field(..., description="Concentração do medicamento")
    posologia: str = Field(..., description="Posologia detalhada")
    via: str = Field(..., description="Via de administração")
    frequencia: str = Field(..., description="Frequência de administração")
    duracao: str = Field(..., description="Duração do tratamento")
    ajustes: Optional[str] = Field(None, description="Ajustes feitos pelo médico")
    observacoes: Optional[str] = Field(None, description="Observações adicionais")

    @field_validator('nome', 'principio_ativo', 'forma', 'concentracao', 'posologia', 'via', 'frequencia', 'duracao')
    @classmethod
    def validate_required_fields(cls, v):
        if not v or not v.strip():
            raise ValueError("Campo obrigatório não pode estar vazio")
        return v.strip()


class SourceSchema(BaseModel):
    """Schema para fontes de informação usadas pela IA"""
    source_id: str = Field(..., description="ID único da fonte no banco de dados")
    source_type: str = Field(..., description="Tipo: PCDT, GUIDELINE, BULA")
    title: str = Field(..., description="Título da fonte")
    version_date: Optional[date] = Field(None, description="Data da versão")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de confiança (0-1)")


class PrescriptionResponseSchema(BaseModel):
    """Schema completo da resposta da IA para prescrição"""
    resumo_tecnico_medico: List[str] = Field(
        ..., 
        description="Resumo técnico para o médico",
        min_length=1
    )
    orientacoes_ao_paciente: List[str] = Field(
        ..., 
        description="Orientações para o paciente",
        min_length=1
    )
    medicamentos: List[MedicationSchema] = Field(
        ..., 
        description="Lista de medicamentos prescritos",
        min_length=1
    )
    alertas_seguranca: List[str] = Field(
        ..., 
        description="Alertas de segurança",
        default_factory=list
    )
    monitorizacao: List[str] = Field(
        ..., 
        description="Itens de monitorização necessários",
        default_factory=list
    )
    fontes: List[SourceSchema] = Field(
        ..., 
        description="Fontes consultadas pela IA",
        min_length=1
    )

    @field_validator('medicamentos')
    @classmethod
    def validate_medications(cls, v):
        if not v or len(v) == 0:
            raise ValueError("Pelo menos um medicamento deve ser prescrito")
        return v


class DoctorInputSchema(BaseModel):
    """Schema para entrada do médico (sintomas/diagnóstico)"""
    sintomas: str = Field(..., description="Sintomas relatados", min_length=10)
    diagnostico: Optional[str] = Field(None, description="Diagnóstico (se disponível)")
    historico_relevante: Optional[str] = Field(None, description="Histórico médico relevante")
    alergias: Optional[List[str]] = Field(None, description="Lista de alergias conhecidas")
    gravidez: Optional[bool] = Field(None, description="Indica se paciente está grávida")
    idade_paciente: Optional[int] = Field(None, ge=0, le=150, description="Idade do paciente")
    peso: Optional[float] = Field(None, gt=0, description="Peso do paciente em kg")
    altura: Optional[float] = Field(None, gt=0, description="Altura do paciente em cm")
    comorbidades: Optional[List[str]] = Field(None, description="Comorbidades conhecidas")
    medicamentos_atuais: Optional[List[str]] = Field(None, description="Medicamentos em uso atual")

    @field_validator('sintomas')
    @classmethod
    def validate_symptoms(cls, v):
        if not v or len(v.strip()) < 10:
            raise ValueError("Sintomas devem ter pelo menos 10 caracteres")
        return v.strip()


class DoctorInputSanitizedSchema(BaseModel):
    """Schema para entrada sanitizada (sem PII) - usado internamente"""
    sintomas: str
    diagnostico: Optional[str] = None
    historico_relevante: Optional[str] = None
    alergias: Optional[List[str]] = None
    gravidez: Optional[bool] = None
    idade_paciente: Optional[int] = None
    peso: Optional[float] = None
    altura: Optional[float] = None
    comorbidades: Optional[List[str]] = None
    medicamentos_atuais: Optional[List[str]] = None
    # Campos PII removidos: nome, cpf, telefone, email, endereco


class PrescriptionEditSchema(BaseModel):
    """Schema para edições feitas pelo médico na prescrição sugerida"""
    medicamento_index: int = Field(..., ge=0, description="Índice do medicamento editado")
    campo_editado: str = Field(..., description="Nome do campo editado")
    valor_original: str = Field(..., description="Valor original sugerido pela IA")
    valor_editado: str = Field(..., description="Valor editado pelo médico")
    motivo: Optional[str] = Field(None, description="Motivo da edição (opcional)")


class AuditTrailEntrySchema(BaseModel):
    """Schema para entrada no audit trail (validação antes de salvar)"""
    action: ActionType = Field(..., description="Tipo de ação registrada")
    consulta_id: Optional[int] = Field(None, description="ID da consulta relacionada")
    receita_id: Optional[int] = Field(None, description="ID da receita relacionada")
    input_data: Optional[dict] = Field(None, description="Dados de entrada (sanitizados)")
    ai_suggestion: Optional[dict] = Field(None, description="Sugestão da IA (JSON)")
    doctor_edit: Optional[PrescriptionEditSchema] = Field(None, description="Edição do médico")
    final_prescription: Optional[dict] = Field(None, description="Prescrição final (JSON)")
    pdf_hash: Optional[str] = Field(None, description="Hash SHA-256 do PDF gerado")
    source_ids_used: Optional[List[str]] = Field(None, description="IDs das fontes usadas pela IA")
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Score de confiança da IA")
    manual_override_reason: Optional[str] = Field(None, description="Motivo de override manual")
    break_glass_confirmed: Optional[bool] = Field(None, description="Confirmação de break glass")
    ip_address: Optional[str] = Field(None, description="Endereço IP da requisição")
    user_agent: Optional[str] = Field(None, description="User agent do navegador")

    @field_validator('action')
    @classmethod
    def validate_action_required_fields(cls, v, info):
        """Valida campos obrigatórios baseado no tipo de ação"""
        data = info.data
        if v == ActionType.INPUT_RECEIVED and not data.get('input_data'):
            raise ValueError("input_data é obrigatório para INPUT_RECEIVED")
        if v == ActionType.AI_SUGGESTION_GENERATED and not data.get('ai_suggestion'):
            raise ValueError("ai_suggestion é obrigatório para AI_SUGGESTION_GENERATED")
        if v == ActionType.DOCTOR_EDIT and not data.get('doctor_edit'):
            raise ValueError("doctor_edit é obrigatório para DOCTOR_EDIT")
        if v == ActionType.PRESCRIPTION_FINALIZED and not data.get('final_prescription'):
            raise ValueError("final_prescription é obrigatório para PRESCRIPTION_FINALIZED")
        if v == ActionType.PDF_GENERATED and not data.get('pdf_hash'):
            raise ValueError("pdf_hash é obrigatório para PDF_GENERATED")
        return v


class PrescriptionFinalSchema(BaseModel):
    """Schema para prescrição final validada antes de gerar PDF"""
    consulta_id: int = Field(..., description="ID da consulta")
    medicamentos: List[MedicationSchema] = Field(..., min_length=1)
    resumo_tecnico_medico: List[str] = Field(..., min_length=1)
    orientacoes_ao_paciente: List[str] = Field(..., min_length=1)
    alertas_seguranca: List[str] = Field(default_factory=list)
    monitorizacao: List[str] = Field(default_factory=list)
    fontes: List[SourceSchema] = Field(..., min_length=1)
    assinado_por: int = Field(..., description="ID do médico que assinou")
    assinado_em: datetime = Field(default_factory=datetime.now, description="Data/hora da assinatura")
    versao: int = Field(default=1, ge=1, description="Versão da prescrição")
