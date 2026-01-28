-- ============================================================================
-- SmartRx AI - Script de Inicialização do Banco de Dados
-- Este script é executado automaticamente quando o container PostgreSQL inicia
-- ============================================================================

-- Habilita a extensão para vetores (Essencial para o RAG/IA)
CREATE EXTENSION IF NOT EXISTS vector;
-- Habilita UUID para IDs seguros
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. TABELA DE MÉDICOS (Users)
-- Integra com o modelo Usuario existente do Django
-- ============================================================================
CREATE TABLE IF NOT EXISTS doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL,
    crm VARCHAR(20) NOT NULL UNIQUE, -- Registro Médico
    uf_crm VARCHAR(2) NOT NULL, -- Estado do CRM
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 2. BASE DE CONHECIMENTO (O "Cérebro" do RAG)
-- Aqui ficam os pedaços (chunks) das bulas e protocolos
-- ============================================================================
CREATE TABLE IF NOT EXISTS knowledge_base (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL, -- O texto real (ex: "A dosagem para adultos é...")
    embedding vector(1536), -- Vetor da OpenAI (text-embedding-3-small)
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('OFFICIAL_PROTOCOL', 'MEDICAL_SOCIETY', 'DRUG_LEAFLET')),
    source_title VARCHAR(255) NOT NULL, -- Ex: "PCDT de Hipertensão 2024"
    source_id VARCHAR(255), -- ID único da fonte (para rastreabilidade)
    version_date DATE, -- Para expirar protocolos antigos
    validity_status VARCHAR(20) DEFAULT 'ACTIVE' CHECK (validity_status IN ('ACTIVE', 'EXPIRED', 'DEPRECATED')),
    metadata JSONB, -- Ex: {"is_pediatric": true, "pregnancy_category": "B", "tier": 1}
    hospital_id INTEGER, -- Opcional: conhecimento específico do hospital
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexação para busca vetorial rápida (HNSW - Hierarchical Navigable Small World)
-- Usa IF NOT EXISTS para evitar erros em reinicializações
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'knowledge_base_embedding_idx'
    ) THEN
        CREATE INDEX knowledge_base_embedding_idx ON knowledge_base 
            USING hnsw (embedding vector_cosine_ops);
    END IF;
END $$;

-- Índices adicionais para filtros
CREATE INDEX IF NOT EXISTS knowledge_base_source_type_idx ON knowledge_base (source_type);
CREATE INDEX IF NOT EXISTS knowledge_base_validity_status_idx ON knowledge_base (validity_status);
CREATE INDEX IF NOT EXISTS knowledge_base_hospital_id_idx ON knowledge_base (hospital_id) WHERE hospital_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS knowledge_base_metadata_idx ON knowledge_base USING GIN (metadata);

-- Comentários para documentação
COMMENT ON TABLE knowledge_base IS 'Armazena fragmentos de bulas e protocolos vetorizados para busca semântica.';
COMMENT ON COLUMN knowledge_base.embedding IS 'Vetor de embedding (1536 dimensões) gerado pela OpenAI text-embedding-3-small';
COMMENT ON COLUMN knowledge_base.source_type IS 'Tipo da fonte: OFFICIAL_PROTOCOL (Tier 1), MEDICAL_SOCIETY (Tier 2), DRUG_LEAFLET (Tier 3)';
COMMENT ON COLUMN knowledge_base.metadata IS 'Metadados adicionais em JSON: tier, pregnancy_category, is_pediatric, etc.';

-- ============================================================================
-- 3. CONSULTAS (Sessões)
-- Integra com o modelo Consulta existente do Django
-- ============================================================================
CREATE TABLE IF NOT EXISTS consultations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doctor_id UUID REFERENCES doctors(id),
    anonymized_patient_id VARCHAR(100), -- ID interno, sem Nome/CPF aqui (LGPD compliant)
    symptoms_input TEXT, -- O que o médico digitou (já sanitizado)
    diagnosis_input TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- 4. PRESCRIÇÕES (O Resultado)
-- Integra com o modelo Receita existente do Django
-- ============================================================================
CREATE TABLE IF NOT EXISTS prescriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consultation_id UUID REFERENCES consultations(id),
    medication_name VARCHAR(255) NOT NULL,
    dosage TEXT NOT NULL,
    patient_instructions TEXT NOT NULL, -- A parte "humanizada"
    
    -- Rastreabilidade de IA vs Humano (CRÍTICO para responsabilidade civil)
    is_ai_generated BOOLEAN DEFAULT TRUE,
    was_edited_by_doctor BOOLEAN DEFAULT FALSE, -- Flag CRÍTICA para defesa jurídica
    ai_confidence_score FLOAT, -- Score de confiança da IA (0.0 a 1.0)
    source_ids_used TEXT[], -- Array de source_ids das fontes consultadas
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comentários críticos para compliance
COMMENT ON TABLE prescriptions IS 'Prescrições geradas pelo sistema. Cada campo editado pelo médico deve ser rastreado.';
COMMENT ON COLUMN prescriptions.was_edited_by_doctor IS 'Indica se o médico alterou a sugestão original da IA. Crucial para defesa jurídica conforme RDC 657/2022.';
COMMENT ON COLUMN prescriptions.is_ai_generated IS 'Indica se a prescrição foi gerada pela IA ou criada manualmente pelo médico.';
COMMENT ON COLUMN prescriptions.source_ids_used IS 'Lista de IDs das fontes (knowledge_base) consultadas pela IA para gerar esta prescrição.';

-- ============================================================================
-- 5. LOGS DE AUDITORIA (A "Caixa Preta" Jurídica)
-- Registra cada passo. Imutável.
-- Integra com o modelo AuditLog existente do Django
-- ============================================================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    consultation_id UUID REFERENCES consultations(id),
    actor_type VARCHAR(20) CHECK (actor_type IN ('AI_SYSTEM', 'DOCTOR')),
    action_type VARCHAR(50) NOT NULL, -- Ex: "SUGGESTION_GENERATED", "DOSAGE_EDITED", "PDF_SIGNED"
    
    -- Armazena o "antes" e "depois" em JSON para flexibilidade
    payload JSONB, 
    
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Índices para queries de auditoria
CREATE INDEX IF NOT EXISTS audit_logs_consultation_id_idx ON audit_logs (consultation_id);
CREATE INDEX IF NOT EXISTS audit_logs_action_type_idx ON audit_logs (action_type);
CREATE INDEX IF NOT EXISTS audit_logs_timestamp_idx ON audit_logs (timestamp);
CREATE INDEX IF NOT EXISTS audit_logs_actor_type_idx ON audit_logs (actor_type);

COMMENT ON TABLE audit_logs IS 'Registro imutável de todas as ações para fins de compliance e auditoria. Conforme ANVISA RDC 657/2022.';
COMMENT ON COLUMN audit_logs.payload IS 'Dados da ação em JSON: input_data, ai_suggestion, doctor_edit, final_prescription, etc.';

-- ============================================================================
-- VIEWS ÚTEIS PARA RELATÓRIOS
-- ============================================================================

-- View para prescrições com rastreabilidade completa
CREATE OR REPLACE VIEW prescriptions_with_traceability AS
SELECT 
    p.id,
    p.medication_name,
    p.dosage,
    p.is_ai_generated,
    p.was_edited_by_doctor,
    p.ai_confidence_score,
    p.source_ids_used,
    c.symptoms_input,
    c.diagnosis_input,
    d.full_name as doctor_name,
    d.crm,
    p.created_at
FROM prescriptions p
JOIN consultations c ON p.consultation_id = c.id
JOIN doctors d ON c.doctor_id = d.id;

-- View para estatísticas de uso da IA
CREATE OR REPLACE VIEW ai_usage_stats AS
SELECT 
    COUNT(*) as total_prescriptions,
    COUNT(*) FILTER (WHERE is_ai_generated = TRUE) as ai_generated,
    COUNT(*) FILTER (WHERE was_edited_by_doctor = TRUE) as doctor_edited,
    AVG(ai_confidence_score) as avg_confidence_score,
    DATE_TRUNC('day', created_at) as date
FROM prescriptions
GROUP BY DATE_TRUNC('day', created_at)
ORDER BY date DESC;

-- ============================================================================
-- MENSAGEM DE SUCESSO
-- ============================================================================
DO $$
BEGIN
    RAISE NOTICE 'Schema SmartRx AI inicializado com sucesso!';
    RAISE NOTICE 'Tabelas criadas: doctors, knowledge_base, consultations, prescriptions, audit_logs';
    RAISE NOTICE 'Extensões habilitadas: vector, uuid-ossp';
END $$;
