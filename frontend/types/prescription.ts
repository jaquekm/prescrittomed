export interface Medication {
  nome: string;
  principio_ativo: string;
  forma: string;
  concentracao: string;
  posologia: string;
  via: string;
  frequencia: string;
  duracao: string;
  observacoes?: string | null;
}

export interface Source {
  source_id: string;
  source_type: string;
  title: string;
  confidence_score?: number | null;
}

export interface PrescriptionResponse {
  medicamentos: Medication[];
  resumo_tecnico_medico: string[];
  orientacoes_ao_paciente: string[];
  alertas_seguranca: string[];
  monitorizacao: string[];
  fontes: Source[];
  confidence_score?: number | null;
}

export interface PrescriptionRequest {
  symptoms: string;
  diagnosis?: string;
}
