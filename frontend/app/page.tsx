"use client";

import React, { useState } from 'react';
import { Activity, Pill, Check, Wand2, Stethoscope, Printer, AlertTriangle } from 'lucide-react';

export default function Dashboard() {
  const [symptoms, setSymptoms] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [selectedMeds, setSelectedMeds] = useState<string[]>([]);
  const [error, setError] = useState('');

  const handleGenerate = async () => {
    setIsLoading(true);
    setError('');
    setResult(null);
    setSelectedMeds([]);

    try {
      console.log("🚀 Enviando pedido ao Python...");
      
      const response = await fetch('http://127.0.0.1:8000/api/v1/prescribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          symptoms: symptoms,
          diagnosis: diagnosis || null
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Erro do Servidor (${response.status}): ${errorText}`);
      }

      const data = await response.json();
      console.log("📦 DADOS RECEBIDOS (RAW):", data); // Olhe o console do navegador (F12)

      // --- LÓGICA DE NORMALIZAÇÃO (O SEGREDO PARA NÃO QUEBRAR) ---
      // Tenta encontrar a lista de remédios onde quer que a IA tenha colocado
      let listaParaExibir = [];

      if (data.prescricoes && Array.isArray(data.prescricoes)) {
        listaParaExibir = data.prescricoes;
      } else if (data.medicamentos && Array.isArray(data.medicamentos)) {
        listaParaExibir = data.medicamentos;
      } else if (Array.isArray(data)) {
        listaParaExibir = data;
      }

      if (listaParaExibir.length === 0) {
        throw new Error("A IA respondeu, mas não encontrei a lista de medicamentos no formato esperado.");
      }

      // Salva no estado já normalizado
      setResult({ prescricoes: listaParaExibir });
      
    } catch (err: any) {
      console.error("❌ ERRO NO FRONT:", err);
      setError(err.message || 'Erro desconhecido ao processar resposta.');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleMedication = (medName: string) => {
    if (selectedMeds.includes(medName)) {
      setSelectedMeds(selectedMeds.filter(name => name !== medName));
    } else {
      setSelectedMeds([...selectedMeds, medName]);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans text-slate-800">
      
      {/* HEADER */}
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-emerald-900 flex items-center gap-2">
            <Activity className="h-6 w-6 text-emerald-600" />
            PrescrittoMED <span className="text-sm font-normal text-emerald-600 bg-emerald-100 px-2 py-1 rounded-full">AI Beta</span>
          </h1>
        </div>
        {selectedMeds.length > 0 && (
          <div className="bg-emerald-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 shadow-lg animate-in fade-in slide-in-from-top-2">
            <Printer className="h-4 w-4" />
            <span className="font-bold">{selectedMeds.length}</span> na receita
          </div>
        )}
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* --- COLUNA ESQUERDA: INPUTS --- */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="bg-emerald-900/5 p-4 border-b border-slate-100 flex items-center gap-2">
              <Stethoscope className="h-5 w-5 text-emerald-700" />
              <h2 className="font-semibold text-emerald-900">Anamnese</h2>
            </div>
            
            <div className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Sintomas</label>
                <textarea 
                  value={symptoms}
                  onChange={(e) => setSymptoms(e.target.value)}
                  placeholder="Ex: Paciente com dor de garganta forte, febre de 39 graus..."
                  className="w-full h-32 p-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 text-sm resize-none"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">Diagnóstico (Opcional)</label>
                <input 
                  type="text"
                  value={diagnosis}
                  onChange={(e) => setDiagnosis(e.target.value)}
                  placeholder="Ex: Amigdalite Bacteriana"
                  className="w-full p-3 rounded-lg border border-slate-300 focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>

              {error && (
                <div className="bg-red-50 text-red-600 p-3 rounded-lg text-sm border border-red-200 flex gap-2 items-start animate-in fade-in">
                  <AlertTriangle className="h-5 w-5 shrink-0 mt-0.5" />
                  <div>{error}</div>
                </div>
              )}

              <button 
                onClick={handleGenerate}
                disabled={isLoading || !symptoms}
                className={`w-full py-3 px-4 rounded-lg flex items-center justify-center gap-2 text-white font-medium transition-all shadow-md
                  ${isLoading || !symptoms ? 'bg-slate-300 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700 hover:shadow-lg hover:-translate-y-0.5'}
                `}
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    Analisando Clínca...
                  </>
                ) : (
                  <>
                    <Wand2 className="h-5 w-5" />
                    Gerar Prescrição Inteligente
                  </>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* --- COLUNA DIREITA: RESULTADOS --- */}
        <div className="lg:col-span-7">
          {!result && !isLoading && (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 border-2 border-dashed border-slate-200 rounded-xl p-12 bg-slate-50/50">
              <Activity className="h-16 w-16 mb-4 text-slate-300" />
              <p>Descreva o caso clínico para iniciar.</p>
            </div>
          )}

          {result && result.prescricoes && (
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-700">
              <h3 className="text-lg font-bold text-slate-700 mb-4 px-1">Sugestão Terapêutica</h3>
              
              {result.prescricoes.map((item: any, index: number) => {
                // --- LÓGICA DE EXIBIÇÃO ROBUSTA ---
                // Verifica várias chaves possíveis para o NOME
                const medNome = item.medicamento?.nome || item.nome_medicamento || item.nome || "Medicamento (Nome não identificado)";
                
                // Verifica várias chaves possíveis para a POSOLOGIA
                let medPosologia = "Verificar na bula";
                if (item.resumo?.como_usar_posologia) {
                   medPosologia = Array.isArray(item.resumo.como_usar_posologia) 
                      ? item.resumo.como_usar_posologia[0] 
                      : item.resumo.como_usar_posologia;
                } else if (item.posologia) {
                   medPosologia = item.posologia;
                }

                // Verifica várias chaves possíveis para a NOTA
                const nota = item.nota_fixa || item.instrucao || item.observacao || item.orientacao || "Siga orientações médicas padrão.";
                
                const isSelected = selectedMeds.includes(medNome);
                
                return (
                  <div key={index} className={`rounded-xl shadow-sm border transition-all overflow-hidden bg-white
                    ${isSelected ? 'border-emerald-500 ring-1 ring-emerald-500 shadow-md' : 'border-slate-200 hover:shadow-md'}
                  `}>
                    {/* Cabeçalho do Card */}
                    <div className="p-4 flex justify-between items-start border-b border-slate-50">
                      <div>
                        <h4 className="text-lg font-bold text-slate-900">{medNome}</h4>
                        <p className="text-sm text-slate-500 mt-1 font-medium">{medPosologia}</p>
                      </div>
                      <button 
                        onClick={() => toggleMedication(medNome)}
                        className={`p-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors
                          ${isSelected ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-500 hover:bg-emerald-100 hover:text-emerald-700'}
                        `}
                      >
                         {isSelected ? <><Check className="h-4 w-4" /> Aprovado</> : "Aprovar"}
                      </button>
                    </div>
                    {/* Corpo do Card (Nota) */}
                    <div className="p-4 bg-blue-50/50">
                       <div className="flex gap-3 items-start">
                          <Pill className="h-4 w-4 text-blue-500 mt-1 shrink-0" />
                          <p className="text-sm text-blue-800 leading-relaxed">{nota}</p>
                       </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}