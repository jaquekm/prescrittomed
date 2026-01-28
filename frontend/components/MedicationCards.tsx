'use client';

import { PrescriptionResponse } from '@/types/prescription';
import MedicationCard from './MedicationCard';

interface MedicationCardsProps {
  prescription: PrescriptionResponse;
}

export default function MedicationCards({ prescription }: MedicationCardsProps) {
  return (
    <div className="space-y-6">
      {/* Header com informações gerais */}
      <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200">
        <h2 className="text-xl font-semibold text-gray-900 mb-4">
          Prescrição Gerada
        </h2>
        
        {prescription.confidence_score && (
          <div className="mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-gray-700">Confiança:</span>
              <div className="flex-1 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-primary-600 h-2 rounded-full transition-all"
                  style={{ width: `${prescription.confidence_score * 100}%` }}
                ></div>
              </div>
              <span className="text-sm text-gray-600">
                {(prescription.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
          </div>
        )}

        {/* Resumo Técnico */}
        {prescription.resumo_tecnico_medico && prescription.resumo_tecnico_medico.length > 0 && (
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Resumo Técnico</h3>
            <ul className="list-disc list-inside text-sm text-gray-600 space-y-1">
              {prescription.resumo_tecnico_medico.map((item, index) => (
                <li key={index}>{item}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Fontes */}
        {prescription.fontes && prescription.fontes.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-gray-700 mb-2">Fontes Consultadas</h3>
            <div className="flex flex-wrap gap-2">
              {prescription.fontes.map((fonte, index) => (
                <span
                  key={index}
                  className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                >
                  {fonte.title}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Cards de Medicamentos */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold text-gray-900">
          Medicamentos ({prescription.medicamentos.length})
        </h2>
        
        {prescription.medicamentos.map((medication, index) => (
          <MedicationCard key={index} medication={medication} />
        ))}
      </div>

      {/* Orientações ao Paciente */}
      {prescription.orientacoes_ao_paciente && prescription.orientacoes_ao_paciente.length > 0 && (
        <div className="bg-blue-50 rounded-lg shadow-sm p-6 border border-blue-200">
          <h3 className="text-lg font-semibold text-blue-900 mb-3">
            Orientações ao Paciente
          </h3>
          <ul className="list-disc list-inside text-sm text-blue-800 space-y-2">
            {prescription.orientacoes_ao_paciente.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Alertas de Segurança */}
      {prescription.alertas_seguranca && prescription.alertas_seguranca.length > 0 && (
        <div className="bg-red-50 rounded-lg shadow-sm p-6 border border-red-200">
          <h3 className="text-lg font-semibold text-red-900 mb-3">
            ⚠️ Alertas de Segurança
          </h3>
          <ul className="list-disc list-inside text-sm text-red-800 space-y-2">
            {prescription.alertas_seguranca.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Monitorização */}
      {prescription.monitorizacao && prescription.monitorizacao.length > 0 && (
        <div className="bg-yellow-50 rounded-lg shadow-sm p-6 border border-yellow-200">
          <h3 className="text-lg font-semibold text-yellow-900 mb-3">
            Monitorização
          </h3>
          <ul className="list-disc list-inside text-sm text-yellow-800 space-y-2">
            {prescription.monitorizacao.map((item, index) => (
              <li key={index}>{item}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
