"use client";

import React, { useState } from 'react';
import { Mail, Lock, ArrowRight, Stethoscope, CheckCircle2, Fingerprint } from 'lucide-react';
import { supabase } from '@/lib/supabaseClient'; 

interface LoginScreenProps {
  onLoginSuccess: () => void;
}

export default function LoginScreen({ onLoginSuccess }: LoginScreenProps) {
  const [loading, setLoading] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
        const { data, error } = await supabase.auth.signInWithPassword({
            email: email,
            password: password,
        });

        if (error) {
            alert("Erro: " + error.message);
            setLoading(false);
            return;
        }

        if (data.session) {
            console.log("Logado com sucesso!", data);
            localStorage.setItem('prescritto_token', data.session.access_token);
            onLoginSuccess();
        }

    } catch (err) {
        alert("Ocorreu um erro inesperado.");
        setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex bg-white font-sans">
      
      {/* LADO ESQUERDO (Verde Bonito) */}
      <div className="hidden lg:flex w-1/2 bg-emerald-900 relative flex-col justify-between p-12 overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-10">
            <svg className="h-full w-full" viewBox="0 0 100 100" preserveAspectRatio="none">
                <path d="M0 100 C 20 0 50 0 100 100 Z" fill="white" />
            </svg>
        </div>

        <div className="relative z-10">
            <div className="flex items-center gap-3 mb-8">
               <div className="bg-emerald-500/20 p-2 rounded-lg backdrop-blur-sm border border-emerald-500/30">
                 <Stethoscope className="h-6 w-6 text-emerald-100" />
               </div>
               {/* Removi o "AI" daqui também para manter o padrão que você pediu */}
               <span className="text-2xl font-bold text-white tracking-tight">PrescrittoMED</span>
            </div>

            <h1 className="text-5xl font-bold text-white leading-tight mb-6">
                Acesse sua conta <br/>
                <span className="text-emerald-400">Profissional.</span>
            </h1>
        </div>

        <div className="relative z-10 grid grid-cols-2 gap-6">
            <div className="flex items-center gap-3 text-emerald-100">
                <div className="bg-emerald-800 p-2 rounded-full"><CheckCircle2 className="h-5 w-5" /></div>
                <span className="text-sm font-medium">Protocolos Vigentes</span>
            </div>
            <div className="flex items-center gap-3 text-emerald-100">
                <div className="bg-emerald-800 p-2 rounded-full"><Fingerprint className="h-5 w-5" /></div>
                <span className="text-sm font-medium">Segurança de Dados</span>
            </div>
        </div>
      </div>

      {/* LADO DIREITO (Formulário Real) */}
      <div className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 bg-slate-50">
        <div className="w-full max-w-[400px] bg-white p-8 rounded-2xl shadow-xl border border-slate-100">
            
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold text-slate-800">Bem-vindo(a)</h2>
                <p className="text-slate-500 text-sm mt-2">Insira suas credenciais de acesso.</p>
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
                {/* Campo Email */}
                <div className="relative">
                    <Mail className="absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
                    <input 
                        type="email" 
                        placeholder="E-mail"
                        required
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        // ADICIONEI text-black AQUI
                        className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm transition-all text-black"
                    />
                </div>

                {/* Campo Senha */}
                <div className="relative">
                    <Lock className="absolute left-3 top-3.5 h-5 w-5 text-slate-400" />
                    <input 
                        type="password" 
                        placeholder="Senha"
                        required
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        // ADICIONEI text-black AQUI
                        className="w-full pl-10 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-sm transition-all text-black"
                    />
                </div>

                <button 
                    type="submit"
                    disabled={loading}
                    className="w-full py-3 bg-emerald-600 hover:bg-emerald-700 text-white font-bold rounded-lg shadow-lg transition-all flex justify-center items-center gap-2"
                >
                    {loading ? 'Verificando...' : <>Entrar <ArrowRight className="h-4 w-4" /></>}
                </button>
            </form>

            <p className="mt-8 text-center text-xs text-slate-400">
                Ainda não tem conta? Peça ao administrador para criar seu usuário no Painel Supabase.
            </p>

        </div>
      </div>
    </div>
  );
}