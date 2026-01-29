"use client";

import React, { useState, useEffect } from 'react';
import LoginScreen from '../components/LoginScreen';
import { supabase } from '../lib/supabaseClient';
// Importando o estetoscópio que você já usa
import { Stethoscope } from 'lucide-react';

function PrescriptionApp({ onLogout }: { onLogout: () => void }) {
  const [sintomas, setSintomas] = useState("");
  const [diagnostico, setDiagnostico] = useState("");
  const [resultado, setResultado] = useState("");
  const [loading, setLoading] = useState(false);

  const handleGerarPrescricao = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResultado("");

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const response = await fetch("http://localhost:8000/api/v1/prescribe", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ symptoms: sintomas, diagnosis: diagnostico }),
      });

      const data = await response.json();
      if (response.ok) {
        setResultado(data.prescription || JSON.stringify(data));
      } else {
        setResultado("Erro: " + (data.detail || "Erro de autenticação"));
      }
    } catch (error) {
      setResultado("Erro de conexão com o servidor Python.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6 md:p-12">
      <div className="max-w-4xl mx-auto">
        
        {/* CABEÇALHO RESTAURADO COM O ESTETOSCÓPIO */}
        <div className="flex justify-between items-center mb-8 bg-white p-6 rounded-xl shadow-sm">
            <div className="flex items-center gap-3">
                {/* O ESTETOSCÓPIO DO LADO DO NOME COMO VOCÊ PEDIU */}
                <div className="bg-emerald-600 p-2 rounded-lg">
                  <Stethoscope className="h-6 w-6 text-white" />
                </div>
                <h1 className="text-3xl font-bold text-emerald-800">
                  PrescrittoMED
                </h1>
            </div>
            
            <button onClick={onLogout} className="text-sm text-red-600 font-semibold px-4 py-2 border border-red-100 rounded-lg hover:bg-red-50">
                Sair / Logout
            </button>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white p-8 rounded-xl shadow-lg border border-slate-100">
                <h2 className="text-lg font-semibold text-slate-700 mb-6">Informações do Atendimento</h2>
                <form onSubmit={handleGerarPrescricao} className="space-y-5">
                    <textarea 
                        className="w-full p-4 border border-slate-200 rounded-xl text-slate-700 font-medium h-32"
                        placeholder="Descreva os sintomas..."
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
                    <button type="submit" disabled={loading} className="w-full bg-emerald-600 text-white font-bold py-4 rounded-xl">
                        {loading ? "Gerando..." : "Gerar Prescrição"}
                    </button>
                </form>
            </div>

            <div className="bg-white p-8 rounded-xl shadow-lg border-2 border-emerald-50 min-h-[400px]">
                <h2 className="text-lg font-semibold text-emerald-800 mb-6">📄 Documento Gerado</h2>
                <div className="text-slate-800 whitespace-pre-wrap text-sm font-medium">
                    {resultado || "Os dados aparecerão aqui."}
                </div>
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