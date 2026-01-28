"use client";

import React, { useState } from 'react';
import { 
  Wand2, 
  Printer, 
  AlertCircle,
  Check,
  Trash2,
  Edit2,
  Info
} from 'lucide-react';
import PrescriptionModal from '@/components/PrescriptionModal';

export default function Dashboard() {
  // --- ESTADOS ---
  const [symptoms, setSymptoms] = useState('');
  const [diagnosis, setDiagnosis] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [selectedMeds, setSelectedMeds] = useState<string[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // --- LÓGICA DE API ---
  const handleGenerate = async () => {
    if (!symptoms) return alert("Por favor, descreva os sintomas.");
    
    setIsLoading(true);
    setResult(null);
    setSelectedMeds([]);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/prescribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symptoms, diagnosis }),
      });

      if (!response.ok) throw new Error("Erro na API");
      const data = await response.json();
      
      let lista = data.prescricoes || data.medicamentos || [];
      setResult({ prescricoes: lista });
      
    } catch (err) {
      alert("Erro ao conectar com a IA. Verifique se o backend está rodando.");
    } finally {
      setIsLoading(false);
    }
  };

  // --- MANIPULAÇÃO DOS CARDS ---
  const toggleAprovar = (medName: string) => {
    if (selectedMeds.includes(medName)) {
      setSelectedMeds(selectedMeds.filter(n => n !== medName));
    } else {
      setSelectedMeds([...selectedMeds, medName]);
    }
  };

  const removerCard = (indexToRemove: number) => {
     if(!result) return;
     const novaLista = result.prescricoes.filter((_: any, idx: number) => idx !== indexToRemove);
     setResult({ ...result, prescricoes: novaLista });
  };

  // Prepara dados para o Modal (PDF)
  const getMedsParaImprimir = () => {
    if (!result?.prescricoes) return [];
    return result.prescricoes
        .filter((item: any) => {
            const nome = item.medicamento?.nome || item.nome_medicamento || item.nome;
            return selectedMeds.includes(nome);
        })
        .map((item: any) => ({
            nome: item.medicamento?.nome || item.nome_medicamento || item.nome,
            // Garante que pegamos a dosagem correta ou um fallback
            dosagem: item.medicamento?.dosagem || item.dosagem || "Verificar Bula",
            quantidade: item.quantidade || "1 unidade",
            // Garante que pegamos o modo de uso
            uso: item.uso || item.posologia || item.modo_de_usar || item.instrucoes || "Conforme orientação médica."
        }));
  };

  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-800">
      
      {/* --- TOPO (VERDE & LOGO NOVA) --- */}
      <nav className="bg-white border-b border-emerald-100 px-8 py-4 flex justify-between items-center sticky top-0 z-20 shadow-sm">
        <div className="flex items-center gap-3">
            {/* SUA LOGO AQUI (Certifique-se de salvar o arquivo em /public/logo-med.png) */}
            <div className="h-10 w-10 relative">
                 {/* Caso a imagem não carregue, use um fallback ou verifique o nome do arquivo */}
                 <img 
                    src="/logo-med.png" 
                    alt="Logo" 
                    className="object-contain h-full w-full"
                    onError={(e) => {
                        e.currentTarget.style.display = 'none'; // Esconde se der erro
                        // Aqui poderia entrar um ícone backup se quisesse
                    }}
                 />
            </div>
            
            <span className="font-bold text-2xl text-slate-800 tracking-tight">
                Prescritto<span className="text-emerald-600">MED</span> AI
            </span>
        </div>
        
        {/* Botão de Gerar Receita (Verde) */}
        {selectedMeds.length > 0 && (
            <button 
                onClick={() => setIsModalOpen(true)}
                className="bg-emerald-600 hover:bg-emerald-700 text-white px-6 py-2.5 rounded-lg font-bold shadow-lg shadow-emerald-200 transition-all flex items-center gap-2 animate-in fade-in slide-in-from-right-4 hover:-translate-y-0.5"
            >
                <Printer className="h-5 w-5" />
                Gerar Receita ({selectedMeds.length})
            </button>
        )}
      </nav>

      <main className="max-w-[1400px] mx-auto p-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* --- COLUNA ESQUERDA: INPUTS --- */}
        <div className="lg:col-span-4 space-y-4">
            <div className="bg-white p-6 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
                <h2 className="text-lg font-bold text-emerald-900 mb-6 flex items-center gap-2 border-b border-slate-50 pb-4">
                    Dados Clínicos
                </h2>
                
                <div className="space-y-5">
                    {/* Campo Sintomas */}
                    <div>
                        <label className="text-xs font-bold text-emerald-700 uppercase tracking-wide mb-2 block">
                            Queixa Principal / Sintomas
                        </label>
                        <textarea 
                            value={symptoms}
                            onChange={(e) => setSymptoms(e.target.value)}
                            className="w-full h-40 p-4 border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none resize-none text-sm leading-relaxed transition-all"
                            placeholder="Descreva os sintomas..."
                        />
                    </div>

                    {/* Campo Diagnóstico (Corrigido) */}
                    <div>
                        <label className="text-xs font-bold text-emerald-700 uppercase tracking-wide mb-2 block">
                            Diagnóstico
                        </label>
                        <input 
                            type="text"
                            value={diagnosis}
                            onChange={(e) => setDiagnosis(e.target.value)}
                            className="w-full p-4 border border-slate-200 rounded-xl bg-slate-50 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 outline-none text-sm font-medium transition-all"
                            placeholder="Ex: Amigdalite Bacteriana"
                        />
                    </div>

                    {/* Botão de Ação Principal (Verde) */}
                    <button 
                        onClick={handleGenerate}
                        disabled={isLoading || !symptoms}
                        className="w-full py-4 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-xl shadow-lg shadow-emerald-200 transition-all flex justify-center items-center gap-2 mt-4 disabled:opacity-70 disabled:cursor-not-allowed transform active:scale-95"
                    >
                        {isLoading ? "Processando..." : <><Wand2 className="h-5 w-5" /> Gerar Prescrição Inteligente</>}
                    </button>
                </div>
            </div>
            
            {/* Aviso */}
            <div className="bg-emerald-50 p-4 rounded-xl border border-emerald-100 flex gap-3">
                <Info className="h-5 w-5 text-emerald-600 flex-shrink-0" />
                <p className="text-xs text-emerald-800 leading-relaxed font-medium">
                    A IA sugere condutas baseadas em protocolos. O médico deve sempre validar a posologia.
                </p>
            </div>
        </div>

        {/* --- COLUNA DIREITA: SUGESTÕES --- */}
        <div className="lg:col-span-8">
            {!result ? (
                // Estado Vazio (Ajustado para tons neutros/verde)
                <div className="h-full min-h-[400px] flex flex-col items-center justify-center text-slate-400 bg-white rounded-3xl border-2 border-dashed border-slate-200">
                    <Wand2 className="h-16 w-16 mb-4 text-emerald-100" />
                    <p className="font-medium text-slate-500">Preencha a anamnese ao lado.</p>
                </div>
            ) : (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-8 duration-500">
                    <div className="flex justify-between items-end px-1">
                        <h3 className="text-xl font-bold text-slate-800">Sugestão Terapêutica</h3>
                        <span className="text-xs font-bold text-emerald-700 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-100">
                            Protocolo Vigente
                        </span>
                    </div>

                    <div className="space-y-4">
                        {result.prescricoes.map((item: any, idx: number) => {
                            // Extração robusta de dados
                            const nome = item.medicamento?.nome || item.nome_medicamento || item.nome;
                            const dosagem = item.medicamento?.dosagem || item.dosagem || "Dose padrão";
                            const instrucoes = item.uso || item.posologia || item.instrucoes || "Instruções não detalhadas.";
                            
                            const isApproved = selectedMeds.includes(nome);

                            return (
                                <div key={idx} className={`bg-white rounded-2xl border transition-all shadow-sm overflow-hidden group
                                    ${isApproved 
                                        ? 'border-emerald-500 ring-1 ring-emerald-500 shadow-md shadow-emerald-50' 
                                        : 'border-slate-200 hover:border-emerald-300 hover:shadow-md'}
                                `}>
                                    <div className="p-6">
                                        {/* Cabeçalho do Card */}
                                        <div className="flex justify-between items-start mb-4">
                                            <div>
                                                <h4 className={`text-xl font-bold mb-1 ${isApproved ? 'text-emerald-800' : 'text-slate-800'}`}>
                                                    {nome}
                                                </h4>
                                                <span className="inline-block bg-slate-100 text-slate-600 text-xs font-bold px-2.5 py-1 rounded border border-slate-200">
                                                    {dosagem}
                                                </span>
                                            </div>
                                            
                                            {item.alerta && (
                                                <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-1 rounded flex items-center gap-1">
                                                    <AlertCircle className="h-3 w-3" /> Atenção
                                                </span>
                                            )}
                                        </div>

                                        {/* Instruções (Corpo) */}
                                        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-slate-600 text-sm leading-relaxed flex gap-3 mb-5">
                                            <Info className="h-5 w-5 text-emerald-500 mt-0.5 flex-shrink-0" />
                                            <p>{instrucoes}</p>
                                        </div>

                                        {/* Botões de Ação (Estilo Verde) */}
                                        <div className="flex justify-end gap-3 pt-2">
                                            <button 
                                                onClick={() => alert("Você poderá editar os detalhes finais na tela de impressão.")}
                                                className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-emerald-700 hover:bg-emerald-50 rounded-lg border border-transparent hover:border-emerald-100 transition-all flex items-center gap-2"
                                            >
                                                <Edit2 className="h-3.5 w-3.5" /> Editar
                                            </button>
                                            
                                            <button 
                                                onClick={() => removerCard(idx)}
                                                className="px-4 py-2 text-xs font-bold text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg border border-transparent hover:border-red-100 transition-all flex items-center gap-2"
                                            >
                                                <Trash2 className="h-3.5 w-3.5" /> Remover
                                            </button>

                                            <button 
                                                onClick={() => toggleAprovar(nome)}
                                                className={`px-6 py-2 text-sm font-bold rounded-lg border transition-all flex items-center gap-2 shadow-sm
                                                    ${isApproved 
                                                        ? 'bg-emerald-600 text-white border-emerald-600 hover:bg-emerald-700' 
                                                        : 'bg-white text-emerald-600 border-emerald-600 hover:bg-emerald-50'}
                                                `}
                                            >
                                                {isApproved ? <><Check className="h-4 w-4" /> Aprovado</> : "Aprovar"}
                                            </button>
                                        </div>
                                    </div>
                                    
                                    {/* Barra Decorativa Inferior se Aprovado */}
                                    {isApproved && <div className="h-1.5 w-full bg-emerald-500"></div>}
                                </div>
                            )
                        })}
                    </div>
                </div>
            )}
        </div>

      </main>

      {/* --- MODAL DE IMPRESSÃO --- */}
      <PrescriptionModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
        medicamentos={getMedsParaImprimir()} 
        diagnosticoInicial={diagnosis}
      />
    </div>
  );
}