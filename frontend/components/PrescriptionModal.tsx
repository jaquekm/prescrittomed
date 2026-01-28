"use client";

import React, { useState, useEffect } from 'react';
import { X, Printer, QrCode, Fingerprint, ChevronRight } from 'lucide-react';

interface PrescriptionModalProps {
  isOpen: boolean;
  onClose: () => void;
  medicamentos: any[];
  diagnosticoInicial: string;
}

export default function PrescriptionModal({ isOpen, onClose, medicamentos, diagnosticoInicial }: PrescriptionModalProps) {
  const [itensEditaveis, setItensEditaveis] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  
  // --- FORMATAÇÃO DE DATA BRASIL (PT-BR) ---
  const dataAtual = new Date();
  const dataFormatada = dataAtual.toLocaleDateString('pt-BR');
  const horaFormatada = dataAtual.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

  useEffect(() => {
    if (isOpen) {
      setItensEditaveis(medicamentos.map(med => ({
        ...med,
        nome: med.nome,
        dosagem: med.dosagem || "Dose padrão", 
        quantidade: med.quantidade || "1 cx", 
        instrucoes: med.uso || med.posologia || med.instrucoes || "Tomar conforme orientação."
      })));
    }
  }, [isOpen, medicamentos]);

  const handleChange = (index: number, field: string, value: string) => {
    const lista = [...itensEditaveis];
    lista[index] = { ...lista[index], [field]: value };
    setItensEditaveis(lista);
  };

  const handleImprimir = () => {
    setLoading(true);
    setTimeout(() => {
        setLoading(false);
        window.print(); 
    }, 1000);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/80 flex items-center justify-center z-[9999] backdrop-blur-sm p-4 overflow-y-auto">
      
      {/* --- FOLHA DE PAPEL A4 --- */}
      <div className="bg-white w-full max-w-[800px] min-h-[90vh] shadow-2xl rounded-sm flex flex-col relative animate-in zoom-in-95 duration-200">
        
        {/* Botão Fechar (Invisível na impressão) */}
        <button 
            onClick={onClose}
            className="absolute top-4 right-4 print:hidden p-2 bg-slate-100 hover:bg-red-100 text-slate-500 hover:text-red-500 rounded-full transition-colors"
        >
            <X className="h-6 w-6" />
        </button>

        {/* --- CONTEÚDO DA RECEITA --- */}
        <div className="p-10 flex-1 flex flex-col font-sans text-slate-800">
            
            {/* 1. CABEÇALHO (Agora com tons de Verde Escuro) */}
            <header className="border-b-2 border-emerald-900 pb-6 mb-8 flex justify-between items-end">
                <div>
                    <div className="flex items-center gap-3 mb-2">
                        {/* Ícone da Clínica em Verde */}
                        <div className="bg-emerald-800 text-white p-2 rounded-lg">
                            <Fingerprint className="h-8 w-8" />
                        </div>
                        <div>
                            <h1 className="text-2xl font-bold tracking-tight text-emerald-950">Dr. Clínica Exemplo</h1>
                            <p className="text-sm text-emerald-700 font-medium">Dr. João Silva - CRM/SP 123456</p>
                        </div>
                    </div>
                </div>
                <div className="text-right text-sm">
                    <p className="font-bold text-slate-700">Paciente: Maria Oliveira</p>
                    {/* Data formatada PT-BR */}
                    <p className="text-slate-500">Data: {dataFormatada}</p>
                    {diagnosticoInicial && (
                         <p className="text-emerald-700 mt-1 font-medium">Dx: {diagnosticoInicial}</p>
                    )}
                </div>
            </header>

            {/* 2. PRESCRIÇÃO TÉCNICA */}
            <section className="mb-10">
                <h3 className="text-lg font-bold text-emerald-950 border-l-4 border-emerald-900 pl-3 mb-4 uppercase tracking-wide">
                    Prescrição Técnica (Uso Farmacêutico)
                </h3>
                
                <div className="space-y-4 ml-2">
                    {itensEditaveis.map((med, idx) => (
                        <div key={idx} className="flex items-start gap-2 group">
                            <span className="font-bold text-slate-400 mt-1">{idx + 1}.</span>
                            <div className="w-full">
                                <div className="flex justify-between items-baseline border-b border-dotted border-slate-300 pb-1">
                                    <input 
                                        value={`${med.nome} ${med.dosagem}`}
                                        onChange={(e) => handleChange(idx, 'nome', e.target.value)} 
                                        className="font-bold text-lg text-slate-900 bg-transparent outline-none w-[70%]"
                                    />
                                    <input 
                                        value={med.quantidade}
                                        onChange={(e) => handleChange(idx, 'quantidade', e.target.value)}
                                        className="text-right text-slate-600 bg-transparent outline-none font-medium w-[25%]"
                                        placeholder="Qtd"
                                    />
                                </div>
                                <div className="text-xs text-slate-400 mt-0.5 italic">
                                    Via Oral • Uso Contínuo
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </section>

            {/* 3. ORIENTAÇÕES (Agora com destaque Verde) */}
            <section className="mb-10 flex-1">
                <h3 className="text-lg font-bold text-emerald-900 border-l-4 border-emerald-500 pl-3 mb-6 uppercase tracking-wide">
                    Orientações ao Paciente
                </h3>

                <div className="space-y-6 bg-slate-50 p-6 rounded-xl border border-slate-100">
                    {itensEditaveis.map((med, idx) => (
                        <div key={idx} className="relative pl-6">
                            {/* Bolinha Verde */}
                            <div className="absolute left-0 top-2 w-2 h-2 rounded-full bg-emerald-500"></div>
                            
                            <h4 className="font-bold text-emerald-800 text-sm mb-1">
                                Sobre o {med.nome}:
                            </h4>
                            <textarea
                                value={med.instrucoes}
                                onChange={(e) => handleChange(idx, 'instrucoes', e.target.value)}
                                rows={2}
                                className="w-full bg-transparent border-none p-0 text-slate-600 text-base leading-relaxed resize-none focus:ring-0"
                            />
                        </div>
                    ))}
                </div>
            </section>

            {/* 4. RODAPÉ (Assinatura) */}
            <footer className="mt-auto pt-6 border-t border-slate-200 flex flex-col md:flex-row justify-between items-center gap-4 text-xs text-slate-500">
                
                <div className="flex items-center gap-3 bg-slate-100 px-4 py-2 rounded border border-slate-200 w-full md:w-auto">
                    <QrCode className="h-10 w-10 text-slate-800" />
                    <div>
                        <p className="font-bold text-slate-700 uppercase">Documento Assinado Digitalmente</p>
                        <p className="font-mono text-[10px] tracking-wider">HASH: 2A3B4C5D6E7F8G9H0I</p>
                        <p className="text-[10px]">Padrão ICP-Brasil • Valide via QR Code</p>
                    </div>
                </div>

                <div className="text-right">
                    <p>Gerado por <span className="font-bold text-emerald-600">PrescrittoMED AI</span></p>
                    {/* Data e Hora em formato PT-BR */}
                    <p>{dataFormatada} às {horaFormatada}</p>
                </div>
            </footer>
        </div>

        {/* --- BARRA FLUTUANTE (Não sai na impressão) --- */}
        <div className="bg-slate-900 text-white p-4 rounded-b-sm flex justify-between items-center print:hidden">
            <span className="text-sm text-slate-400 pl-2">
                * Clique nos textos para editar antes de imprimir.
            </span>
            <div className="flex gap-3">
                <button 
                    onClick={onClose}
                    className="px-4 py-2 hover:bg-slate-700 rounded transition-colors text-sm"
                >
                    Voltar
                </button>
                {/* Botão VERDE ESMERALDA */}
                <button 
                    onClick={handleImprimir}
                    disabled={loading}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded flex items-center gap-2 transition-all shadow-lg"
                >
                    {loading ? "Gerando..." : <><Printer className="h-4 w-4" /> Imprimir / Salvar PDF</>}
                </button>
            </div>
        </div>

      </div>
    </div>
  );
}