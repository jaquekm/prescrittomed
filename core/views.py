from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from openai import OpenAI
from decouple import config
from .models import Paciente, Consulta
from django.contrib import messages
from .forms import NovoMedicoForm, PerfilMedicoForm
from .models import Hospital, PerfilMedico
# Mantenha as outras importações que já estavam lá!

@login_required(login_url='/login/')
def atendimento_medico(request):
    pacientes = Paciente.objects.all()
    
    # Variáveis iniciais
    analise_tecnica = ""
    receita_paciente = ""
    historico_conversa = ""
    paciente_selecionado = None
    consulta_id = request.POST.get('consulta_id')

    if request.method == "POST":
        acao = request.POST.get('acao')
        
        # 1. IDENTIFICA O PACIENTE
        if request.POST.get('paciente'):
            paciente_selecionado = Paciente.objects.get(id=request.POST.get('paciente'))
        elif consulta_id:
            try:
                consulta_temp = Consulta.objects.get(id=consulta_id)
                paciente_selecionado = consulta_temp.paciente
            except Consulta.DoesNotExist:
                paciente_selecionado = None

        # CENÁRIO A: SALVAR EDIÇÃO MANUAL
        if acao == 'salvar_edicao':
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                consulta.prescricao = request.POST.get('receita_editavel')
                consulta.save()
                
                # Recarrega dados
                analise_tecnica = consulta.analise_ia
                receita_paciente = consulta.prescricao
                historico_conversa = consulta.sintomas

        # CENÁRIO B: GERAR COM IA (RASCUNHO)
        elif acao == 'gerar_ia':
            sintomas = request.POST.get('sintomas')
            historico_anterior = request.POST.get('historico_conversa', '')
            
            try:
                client = OpenAI(api_key=config('OPENAI_API_KEY'))
                
                # PROMPT BLINDADO PARA ESTRUTURA
                prompt_sistema = """
                Você é um assistente médico gerando documentos oficiais.
                
                REGRA DE FORMATAÇÃO (OBRIGATÓRIA):
                Você DEVE dividir sua resposta em duas partes usando a tag exata: [DIVISAO]
                
                Parte 1 (Antes da tag): Análise técnica para o médico (hipóteses, conduta).
                Parte 2 (Depois da tag): APENAS o texto da Receita Médica para o paciente.
                
                ESTRUTURA DA RECEITA (Parte 2):
                - Use o padrão brasileiro.
                - Separe por "USO INTERNO" e "USO TÓPICO/EXTERNO" se houver.
                - Lista numerada com Nome do remédio, Dosagem e Posologia.
                - Não inclua cabeçalhos (como nome do hospital), apenas os medicamentos e instruções.
                """
                
                conversa_atual = f"{historico_anterior}\nMédico: {sintomas}"
                
                resposta = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": prompt_sistema},
                        {"role": "user", "content": f"Paciente: {paciente_selecionado.nome_completo if paciente_selecionado else 'N/A'}. \n\nSintomas/Pedido: {conversa_atual}"}
                    ]
                )
                
                conteudo = resposta.choices[0].message.content
                
                # LÓGICA DE SEPARAÇÃO MAIS SEGURA (PLAN B)
                separador = "[DIVISAO]"
                
                if separador in conteudo:
                    partes = conteudo.split(separador)
                    analise_tecnica = partes[0].replace("[TECNICO]", "").strip()
                    receita_paciente = partes[1].replace("[PACIENTE]", "").strip()
                else:
                    # Se a IA falhar na divisão, jogamos tudo no editor para não perder dados
                    analise_tecnica = "A IA não separou a análise da receita. Verifique o texto ao lado."
                    receita_paciente = conteudo 

                historico_conversa = f"{conversa_atual}\nIA: {conteudo}"

                # Salva no banco
                if consulta_id:
                    consulta = Consulta.objects.get(id=consulta_id)
                    consulta.sintomas = historico_conversa
                    consulta.analise_ia = analise_tecnica
                    consulta.prescricao = receita_paciente
                    consulta.save()
                else:
                    nova_consulta = Consulta.objects.create(
                        paciente=paciente_selecionado,
                        medico=request.user,
                        sintomas=historico_conversa,
                        analise_ia=analise_tecnica,
                        prescricao=receita_paciente
                    )
                    consulta_id = nova_consulta.id

            except Exception as e:
                analise_tecnica = f"Erro de conexão: {e}"
                receita_paciente = "Erro ao gerar. Tente novamente."

    return render(request, 'atendimento.html', {
        'analise_tecnica': analise_tecnica,
        'receita_paciente': receita_paciente, # Vai para o editor
        'historico_conversa': historico_conversa,
        'pacientes': pacientes,
        'paciente_selecionado': paciente_selecionado,
        'consulta_id': consulta_id
    })

@login_required(login_url='/login/')
def dashboard(request):
    return render(request, 'dashboard.html')

def gerar_receita(request, consulta_id):
    consulta = Consulta.objects.get(id=consulta_id)
    return render(request, 'receita.html', {'consulta': consulta})
    @login_required(login_url='/login/')
def gestao_hospital(request):
    # 1. Verifica se o usuário é Admin de algum hospital
    try:
        hospital = Hospital.objects.get(admin_responsavel=request.user)
    except Hospital.DoesNotExist:
        return render(request, 'dashboard.html', {'erro': 'Você não tem permissão de gestor.'})

    if request.method == 'POST':
        form = NovoMedicoForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            
            # Verifica se usuário já existe
            if User.objects.filter(username=data['nome_usuario']).exists():
                messages.error(request, "Este nome de usuário já existe.")
            else:
                # Cria o Usuário (Login)
                novo_user = User.objects.create_user(
                    username=data['nome_usuario'],
                    email=data['email'],
                    password=data['senha']
                )
                
                # Cria o Perfil Médico vinculado ao Hospital deste Gestor
                PerfilMedico.objects.create(
                    usuario=novo_user,
                    hospital=hospital,
                    crm=data['crm']
                )
                messages.success(request, f"Dr(a). {data['nome_usuario']} cadastrado com sucesso!")
                return redirect('gestao_hospital')
    else:
        form = NovoMedicoForm()

    # Lista apenas médicos deste hospital
    medicos = PerfilMedico.objects.filter(hospital=hospital)
    
    return render(request, 'gestao_hospital.html', {
        'hospital': hospital,
        'form': form,
        'medicos': medicos
    })

@login_required(login_url='/login/')
def perfil_medico(request):
    try:
        perfil = request.user.perfil_medico
    except PerfilMedico.DoesNotExist:
        messages.error(request, "Seu usuário não tem perfil médico configurado.")
        return redirect('dashboard')

    if request.method == 'POST':
        # request.FILES é obrigatório para upload de imagem
        form = PerfilMedicoForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, "Perfil atualizado com sucesso!")
            return redirect('perfil_medico')
    else:
        form = PerfilMedicoForm(instance=perfil)

    return render(request, 'perfil_medico.html', {'form': form, 'perfil': perfil})