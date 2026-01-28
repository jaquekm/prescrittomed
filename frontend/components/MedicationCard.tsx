import React from 'react';
import { Pill, AlertTriangle, Activity, Info } from 'lucide-react';

interface MedicationCardsProps {
  prescription: any;
}

export default function MedicationCards({ prescription }: MedicationCardsProps) {
  // AQUI ESTAVA O ERRO: Mudamos de .medicamentos para .prescricoes
  if (!prescription || !prescription.prescricoes || prescription.prescricoes.length === 0) {
    return (
      <div className="p-4 bg-yellow-50 text-yellow-700 rounded-lg border border-yellow-200">
        <p className="font-bold">Aguardando prescrição...</p>
        <p className="text-sm">Preencha os sintomas e clique em gerar.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
        <Pill className="h-6 w-6 text-blue-600" />
        Prescrição Sugerida ({prescription.prescricoes.length} itens)
      </h2>

      {prescription.prescricoes.map((item: any, index: number) => {
        const med = item.medicamento;
        const resumo = item.resumo;

        return (
          <div key={index} className="bg-white border border-gray-200 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden">
            {/* Cabeçalho */}
            <div className="bg-slate-50 p-4 border-b border-gray-100 flex justify-between items-start">
              <div>
                <h3 className="text-lg font-bold text-blue-900">{med.nome}</h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs font-medium px-2 py-0.5 rounded bg-blue-100 text-blue-700">
                    {med.fonte || "Fonte ANVISA"}
                  </span>
                </div>
              </div>
            </div>

            {/* Conteúdo */}
            <div className="p-5 space-y-4">
              {/* Posologia (Destaque) */}
              <div className="bg-green-50 p-4 rounded-lg border border-green-100">
                <h4 className="text-sm font-bold text-green-800 flex items-center gap-2 mb-2">
                  <Activity className="h-4 w-4" /> Posologia Recomendada
                </h4>
                <ul className="list-disc list-inside text-sm text-green-900 space-y-1">
                  {resumo.como_usar_posologia?.map((line: string, i: number) => (
                    <li key={i}>{line}</li>
                  ))}
                </ul>
              </div>

              {/* Detalhes Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                <div>
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Indicações</h4>
                  <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                    {resumo.indicacoes_para_que_serve?.slice(0, 3).map((t: string, i: number) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-2">Efeitos Comuns</h4>
                  <ul className="text-sm text-gray-600 space-y-1 list-disc list-inside">
                    {resumo.efeitos_colaterais?.slice(0, 3).map((t: string, i: number) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              </div>

              {/* Alertas */}
              {(resumo.contraindicacoes?.length > 0) && (
                <div className="mt-4 pt-4 border-t border-gray-100">
                  <div className="flex gap-2 items-start text-red-600 bg-red-50 p-3 rounded-md">
                    <AlertTriangle className="h-5 w-5 shrink-0" />
                    <div className="text-sm">
                      <span className="font-bold block mb-1">Atenção / Contraindicações:</span>
                      {resumo.contraindicacoes[0]}
                    </div>
                  </div>
                </div>
              )}
            </div>
            
            <div className="bg-gray-50 px-5 py-2 text-center border-t border-gray-100 text-xs text-gray-400">
               Nota: {item.nota_fixa}
            </div>
          </div>
        );
      })}
    </div>
  );
}