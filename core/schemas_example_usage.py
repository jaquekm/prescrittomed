"""
Exemplos de uso dos Schemas Pydantic - SmartRx AI
Este arquivo demonstra como usar os schemas para validação de dados
"""

from datetime import date, datetime
from core.schemas import (
    DoctorInputSchema,
    DoctorInputSanitizedSchema,
    PrescriptionResponseSchema,
    MedicationSchema,
    SourceSchema,
    PrescriptionEditSchema,
    AuditTrailEntrySchema,
    ActionType,
    PrescriptionFinalSchema,
)


# ============================================================================
# EXEMPLO 1: Validação de entrada do médico
# ============================================================================
def exemplo_validacao_entrada_medico():
    """Exemplo de como validar entrada do médico"""
    
    # Dados de entrada (com PII - será sanitizado antes de enviar à IA)
    dados_entrada = {
        "sintomas": "Paciente apresenta febre alta, tosse seca e dor de cabeça há 3 dias",
        "diagnostico": "Suspected viral infection",
        "idade_paciente": 35,
        "peso": 70.5,
        "altura": 175.0,
        "alergias": ["Penicilina", "Sulfa"],
        "gravidez": False,
        "comorbidades": ["Hipertensão"],
        "medicamentos_atuais": ["Losartana 50mg"]
    }
    
    # Validar usando Pydantic
    entrada_validada = DoctorInputSchema(**dados_entrada)
    print(f"Entrada válida: {entrada_validada.sintomas}")
    
    # Após sanitização (remover PII), criar versão sanitizada
    dados_sanitizados = {
        "sintomas": entrada_validada.sintomas,  # Já sanitizado
        "diagnostico": entrada_validada.diagnostico,
        "idade_paciente": entrada_validada.idade_paciente,
        # PII removido: nome, cpf, telefone, email
    }
    entrada_sanitizada = DoctorInputSanitizedSchema(**dados_sanitizados)
    
    return entrada_sanitizada


# ============================================================================
# EXEMPLO 2: Validação de resposta da IA
# ============================================================================
def exemplo_validacao_resposta_ia():
    """Exemplo de como validar resposta da IA"""
    
    # Resposta simulada da IA (após chamada ao LLM)
    resposta_ia = {
        "resumo_tecnico_medico": [
            "Suspected viral upper respiratory infection",
            "Symptomatic treatment recommended"
        ],
        "orientacoes_ao_paciente": [
            "Repouso relativo",
            "Hidratação adequada",
            "Retornar se piora dos sintomas"
        ],
        "medicamentos": [
            {
                "nome": "Paracetamol",
                "principio_ativo": "Paracetamol",
                "forma": "Comprimido",
                "concentracao": "750mg",
                "posologia": "1 comprimido",
                "via": "Oral",
                "frequencia": "A cada 8 horas",
                "duracao": "5 dias",
                "ajustes": None,
                "observacoes": "Tomar após refeições"
            }
        ],
        "alertas_seguranca": [
            "Não exceder 4g de paracetamol por dia",
            "Evitar álcool durante tratamento"
        ],
        "monitorizacao": [
            "Avaliar resposta ao tratamento em 48h",
            "Monitorar temperatura"
        ],
        "fontes": [
            {
                "source_id": "pcdt_001",
                "source_type": "PCDT",
                "title": "Protocolo Clínico - Infecções Respiratórias",
                "version_date": date(2024, 1, 15),
                "confidence_score": 0.85
            }
        ]
    }
    
    # Validar resposta
    resposta_validada = PrescriptionResponseSchema(**resposta_ia)
    print(f"Medicamentos prescritos: {len(resposta_validada.medicamentos)}")
    
    return resposta_validada


# ============================================================================
# EXEMPLO 3: Registro de edição do médico
# ============================================================================
def exemplo_edicao_medico():
    """Exemplo de como registrar edição do médico"""
    
    edicao = PrescriptionEditSchema(
        medicamento_index=0,
        campo_editado="frequencia",
        valor_original="A cada 8 horas",
        valor_editado="A cada 6 horas",
        motivo="Paciente relata dor intensa, necessário aumento da frequência"
    )
    
    return edicao


# ============================================================================
# EXEMPLO 4: Criação de entrada no Audit Trail
# ============================================================================
def exemplo_audit_trail():
    """Exemplo de como criar entrada no audit trail"""
    
    # Exemplo 1: Input recebido
    audit_input = AuditTrailEntrySchema(
        action=ActionType.INPUT_RECEIVED,
        consulta_id=123,
        input_data={
            "sintomas": "Febre e tosse",
            "idade": 35,
            # Sem PII
        },
        ip_address="192.168.1.100",
        user_agent="Mozilla/5.0..."
    )
    
    # Exemplo 2: Sugestão da IA gerada
    audit_ai = AuditTrailEntrySchema(
        action=ActionType.AI_SUGGESTION_GENERATED,
        consulta_id=123,
        ai_suggestion={
            "medicamentos": [...],
            "fontes": [...]
        },
        source_ids_used=["pcdt_001", "bula_002"],
        confidence_score=0.85,
        modelo_ia="gpt-4o"
    )
    
    # Exemplo 3: Edição do médico
    audit_edit = AuditTrailEntrySchema(
        action=ActionType.DOCTOR_EDIT,
        consulta_id=123,
        doctor_edit={
            "medicamento_index": 0,
            "campo_editado": "dosagem",
            "valor_original": "500mg",
            "valor_editado": "750mg",
            "motivo": "Ajuste baseado em peso do paciente"
        }
    )
    
    # Exemplo 4: Override manual (break glass)
    audit_override = AuditTrailEntrySchema(
        action=ActionType.MANUAL_OVERRIDE,
        consulta_id=123,
        manual_override_reason="Medicamento categoria D prescrito em gestante após confirmação explícita",
        break_glass_confirmed=True
    )
    
    # Exemplo 5: PDF gerado
    audit_pdf = AuditTrailEntrySchema(
        action=ActionType.PDF_GENERATED,
        receita_id=456,
        pdf_hash="a1b2c3d4e5f6...",  # SHA-256
        final_prescription={
            "medicamentos": [...],
            "assinado_por": 789,
            "assinado_em": datetime.now().isoformat()
        }
    )
    
    return audit_input, audit_ai, audit_edit, audit_override, audit_pdf


# ============================================================================
# EXEMPLO 5: Prescrição final antes de gerar PDF
# ============================================================================
def exemplo_prescricao_final():
    """Exemplo de validação da prescrição final antes de gerar PDF"""
    
    prescricao_final = PrescriptionFinalSchema(
        consulta_id=123,
        medicamentos=[
            MedicationSchema(
                nome="Paracetamol",
                principio_ativo="Paracetamol",
                forma="Comprimido",
                concentracao="750mg",
                posologia="1 comprimido",
                via="Oral",
                frequencia="A cada 6 horas",
                duracao="5 dias"
            )
        ],
        resumo_tecnico_medico=["Infecção viral - tratamento sintomático"],
        orientacoes_ao_paciente=["Repouso e hidratação"],
        alertas_seguranca=["Não exceder 4g/dia"],
        monitorizacao=["Avaliar em 48h"],
        fontes=[
            SourceSchema(
                source_id="pcdt_001",
                source_type="PCDT",
                title="Protocolo Clínico",
                confidence_score=0.85
            )
        ],
        assinado_por=789,  # ID do médico
        assinado_em=datetime.now(),
        versao=1
    )
    
    return prescricao_final


# ============================================================================
# EXEMPLO 6: Uso em views/endpoints
# ============================================================================
def exemplo_uso_em_endpoint(dados_brutos):
    """
    Exemplo de como usar os schemas em um endpoint FastAPI/Django
    
    Args:
        dados_brutos: Dados recebidos do request (dict)
    
    Returns:
        Dados validados ou exceção Pydantic
    """
    try:
        # Validar entrada
        entrada = DoctorInputSchema(**dados_brutos)
        
        # Sanitizar (remover PII)
        # ... código de sanitização ...
        
        # Validar resposta da IA
        # resposta_ia = chamar_ia(...)
        # resposta_validada = PrescriptionResponseSchema(**resposta_ia)
        
        return entrada
        
    except Exception as e:
        # PydanticValidationError será levantado se dados inválidos
        raise ValueError(f"Dados inválidos: {e}")


if __name__ == "__main__":
    print("=== Exemplos de uso dos Schemas Pydantic ===\n")
    
    print("1. Validação de entrada do médico:")
    exemplo_validacao_entrada_medico()
    
    print("\n2. Validação de resposta da IA:")
    exemplo_validacao_resposta_ia()
    
    print("\n3. Edição do médico:")
    exemplo_edicao_medico()
    
    print("\n4. Audit Trail:")
    exemplo_audit_trail()
    
    print("\n5. Prescrição final:")
    exemplo_prescricao_final()
    
    print("\n✅ Todos os exemplos executados com sucesso!")
