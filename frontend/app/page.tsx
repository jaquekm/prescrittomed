"use client";

import React, { useState, useEffect } from 'react';
import LoginScreen from '../components/LoginScreen';
import { supabase } from '../lib/supabaseClient';
import { Stethoscope } from 'lucide-react';

function PrescriptionApp({ onLogout }: { onLogout: () => void }) {
  const [sintomas, setSintomas] = useState("");
  const [diagnostico, setDiagnostico] = useState("");
  const [loading, setLoading] = useState(false);
  const [prescricoes, setPrescricoes] = useState<any[]>([]); // Lista limpa

  // 1. Botão VERDE: Consultar IA e mostrar na tela
  const handleGerarPrescricao = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setPrescricoes([]);

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      if (!token) {
         alert("Sessão expirada. Faça login novamente.");
         onLogout();
         return;
      }

      // Envia 'anamnese' para bater com o Python (Resolve erro 422)
      const response = await fetch("http://localhost:8000/api/v1/prescribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ anamnese: sintomas, hipotese: diagnostico }),
      });

      if (response.status === 403) {
         alert("Seu login venceu. Por favor, saia e entre novamente.");
         onLogout();
         return;
      }

      const data = await response.json();
      
      if (data.prescricoes) {
        setPrescricoes(data.prescricoes);
      } else {
        alert("A IA não retornou sugestões válidas.");
      }

    } catch (error) {
      console.error(error);
      alert("Erro de conexão.");
    } finally {
      setLoading(false);
    }
  };

  // 2. Botão PRETO: Baixar PDF com os dados da tela
  const handleBaixarPDF = async () => {
    try {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;

        // Prepara os dados limpos para enviar ao gerador de PDF
        const dadosParaPDF = prescricoes.map((item: any) => ({
            nome: item.medicamento.nome,
            posologia: Array.isArray(item.resumo.como_usar_posologia) ? item.resumo.como_usar_posologia.join(" ") : item.resumo.como_usar_posologia,
            aviso: Array.isArray(item.resumo.advertencias_e_interacoes) ? item.resumo.advertencias_e_interacoes[0] : ""
        }));

        const response = await fetch("http://localhost:8000/api/v1/generate-pdf", {
            method: "POST",
            headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
            body: JSON.stringify({ paciente_nome: "Paciente", medicamentos: dadosParaPDF }),
        });

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = "Receita_Medica.pdf";
        document.body.appendChild(link);
        link.click();
        link.remove();
    } catch (e) {
        alert("Erro ao gerar arquivo PDF.");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12">
      <div className="max-w-5xl mx-auto">
        
        {/* Cabeçalho */}
        <div className="flex justify-between items-center mb-8 bg-white p-6 rounded-xl shadow-sm">
            <div className="flex items-center gap-3">
                <div className="bg-emerald-600 p-2 rounded-lg">
                   <Stethoscope className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-emerald-800">PrescrittoMED</h1>
            </div>
            <button onClick={onLogout} className="text-red-500 font-bold border border-red-100 px-4 py-2 rounded hover:bg-red-50">
                Sair / Logout
            </button>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
            {/* Caixa Esquerda: Input */}
            <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-100">
                <h2 className="text-lg font-semibold text-slate-700 mb-6">Informações do Atendimento</h2>
                <form onSubmit={handleGerarPrescricao} className="space-y-5">
                    <textarea 
                        className="w-full p-4 border border-slate-200 rounded-xl text-slate-700 font-medium h-32"
                        placeholder="Ex: Dor de cabeça forte, febre..."
                        value={sintomas}
                        onChange={(e) => setSintomas(e.target.value)}
                        required
                    />
                    <input 
                        type="text" 
                        className="w-full p-4 border border-slate-200 rounded-xl text-slate-700 font-medium"
                        placeholder="Hipótese Diagnóstica"
                        value={diagnostico}
                        onChange={(e) => setDiagnostico(e.target.value)}
                    />
                    <button type="submit" disabled={loading} className="w-full bg-emerald-600 text-white font-bold py-4 rounded-xl hover:bg-emerald-700 transition-colors">
                        {loading ? "Gerando..." : "1. Analisar Caso"}
                    </button>
                </form>
            </div>

            {/* Caixa Direita: Resultado */}
            <div className="bg-white p-8 rounded-xl shadow-lg border-2 border-emerald-50 min-h-[400px]">
                <h2 className="text-lg font-semibold text-emerald-800 mb-6">📄 Sugestão da IA</h2>
                
                {prescricoes.length === 0 && !loading && (
                    <p className="text-slate-400">Preencha os dados ao lado para ver as sugestões.</p>
                )}

                {/* LISTA DE REMÉDIOS */}
                <div className="space-y-4">
                    {prescricoes.map((item: any, index: number) => (
                        <div key={index} className="border-b border-slate-100 pb-3">
                            <h3 className="font-bold text-emerald-700 text-lg">{item.medicamento.nome}</h3>
                            <p className="text-sm text-slate-600 mt-1">
                                <strong>Posologia:</strong> {
                                    Array.isArray(item.resumo.como_usar_posologia) 
                                    ? item.resumo.como_usar_posologia.join(" ") 
                                    : item.resumo.como_usar_posologia
                                }
                            </p>
                        </div>
                    ))}
                </div>

                {/* BOTÃO DE DOWNLOAD (Só aparece se tiver remédio) */}
                {prescricoes.length > 0 && (
                    <button 
                        onClick={handleBaixarPDF}
                        className="w-full mt-6 bg-slate-800 text-white font-bold py-3 rounded-xl hover:bg-slate-900 flex justify-center items-center gap-2"
                    >
                        ⬇ 2. Baixar Receita PDF
                    </button>
                )}
            </div>
        </div>
      </div>
    </div>
  );
}

export default function Home() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });
    return () => subscription.unsubscribe();
  }, []);

  if (loading) return null;
  if (!session) return <LoginScreen onLoginSuccess={() => {}} />;

  return <PrescriptionApp onLogout={() => supabase.auth.signOut()} />;
}