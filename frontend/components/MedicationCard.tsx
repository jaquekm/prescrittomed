'use client';

import { Medication } from '@/types/prescription';

interface MedicationCardProps {
  medication: Medication;
}

export default function MedicationCard({ medication }: MedicationCardProps) {
  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-gray-900 mb-1">
            {medication.nome}
          </h3>
          <p className="text-sm text-gray-600">
            {medication.principio_ativo}
          </p>
        </div>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
          {medication.concentracao}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Forma</p>
          <p className="text-sm text-gray-900">{medication.forma}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Via</p>
          <p className="text-sm text-gray-900">{medication.via}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Frequência</p>
          <p className="text-sm text-gray-900">{medication.frequencia}</p>
        </div>
        <div>
          <p className="text-xs font-medium text-gray-500 mb-1">Duração</p>
          <p className="text-sm text-gray-900">{medication.duracao}</p>
        </div>
      </div>

      <div className="mb-4">
        <p className="text-xs font-medium text-gray-500 mb-1">Posologia</p>
        <p className="text-sm text-gray-900 font-medium">{medication.posologia}</p>
      </div>

      {medication.observacoes && (
        <div className="pt-4 border-t border-gray-200">
          <p className="text-xs font-medium text-gray-500 mb-1">Observações</p>
          <p className="text-sm text-gray-700">{medication.observacoes}</p>
        </div>
      )}
    </div>
  );
}
