'use client';

import { useState } from 'react';

interface PrescriptionInputProps {
  onPrescribe: (symptoms: string, diagnosis?: string) => void;
  loading: boolean;
}

export default function PrescriptionInput({ onPrescribe, loading }: PrescriptionInputProps) {
  const [symptoms, setSymptoms] = useState('');
  const [diagnosis, setDiagnosis] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (symptoms.trim().length >= 3) {
      onPrescribe(symptoms.trim(), diagnosis.trim() || undefined);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4 flex-1">
      <div>
        <label htmlFor="symptoms" className="block text-sm font-medium text-gray-700 mb-2">
          Sintomas *
        </label>
        <textarea
          id="symptoms"
          value={symptoms}
          onChange={(e) => setSymptoms(e.target.value)}
          placeholder="Ex: Dor de garganta, febre, dificuldade para engolir..."
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
          rows={6}
          required
          minLength={3}
          disabled={loading}
        />
        <p className="mt-1 text-xs text-gray-500">
          Mínimo 3 caracteres
        </p>
      </div>

      <div>
        <label htmlFor="diagnosis" className="block text-sm font-medium text-gray-700 mb-2">
          Diagnóstico (Opcional)
        </label>
        <input
          id="diagnosis"
          type="text"
          value={diagnosis}
          onChange={(e) => setDiagnosis(e.target.value)}
          placeholder="Ex: Amigdalite bacteriana"
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
          disabled={loading}
        />
      </div>

      <button
        type="submit"
        disabled={loading || symptoms.trim().length < 3}
        className="mt-auto w-full bg-primary-600 text-white py-3 px-4 rounded-lg font-medium hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Gerando...
          </span>
        ) : (
          'Gerar Prescrição'
        )}
      </button>
    </form>
  );
}
