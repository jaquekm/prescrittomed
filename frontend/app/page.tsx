'use client';

import { useState } from 'react';
import PrescriptionInput from '@/components/PrescriptionInput';
import MedicationCards from '@/components/MedicationCards';
import Toast from '@/components/Toast';
import { PrescriptionResponse } from '@/types/prescription';

export default function CockpitPage() {
  const [prescription, setPrescription] = useState<PrescriptionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handlePrescribe = async (symptoms: string, diagnosis?: string) => {
    setLoading(true);
    setError(null);
    setPrescription(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/v1/prescribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symptoms,
          diagnosis: diagnosis || undefined,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
        throw new Error(errorData.detail || `Erro ${response.status}: ${response.statusText}`);
      }

      const data: PrescriptionResponse = await response.json();
      setPrescription(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Erro ao gerar prescrição. Tente novamente.';
      setError(errorMessage);
      console.error('Erro ao gerar prescrição:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCloseToast = () => {
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast de erro */}
      {error && <Toast message={error} type="error" onClose={handleCloseToast} />}

      {/* Layout 30/70 */}
      <div className="flex h-screen">
        {/* Painel Esquerdo (30%) - Input */}
        <div className="w-[30%] bg-white border-r border-gray-200 shadow-sm">
          <div className="p-6 h-full flex flex-col">
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                SmartRx AI
              </h1>
              <p className="text-sm text-gray-600">
                Sistema de Apoio à Decisão Clínica
              </p>
              <p className="text-xs text-amber-600 mt-2 font-medium">
                ⚠️ Validação Médica Obrigatória
              </p>
            </div>

            <PrescriptionInput 
              onPrescribe={handlePrescribe} 
              loading={loading}
            />
          </div>
        </div>

        {/* Painel Direito (70%) - Resultados */}
        <div className="flex-1 overflow-y-auto bg-gray-50">
          <div className="p-6">
            {loading && (
              <div className="flex items-center justify-center h-64">
                <div className="text-center">
                  <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mb-4"></div>
                  <p className="text-gray-600">Gerando prescrição...</p>
                </div>
              </div>
            )}

            {!loading && prescription && (
              <MedicationCards prescription={prescription} />
            )}

            {!loading && !prescription && (
              <div className="flex items-center justify-center h-64">
                <div className="text-center text-gray-400">
                  <svg
                    className="mx-auto h-12 w-12 mb-4"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  <p>Digite os sintomas e clique em "Gerar" para ver as prescrições</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
