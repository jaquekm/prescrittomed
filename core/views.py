import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from .forms import ConviteMedicoForm, NovoMedicoForm, PerfilMedicoForm
from .models import AiDraft, AuditLog, Consulta, Hospital, Paciente, PerfilMedico, Receita
from .permissions import get_user_hospital, hospital_scope_required, role_required
from .services.openai_prescription import (
    OpenAIPrescriptionError,
    generate_prescription,
    sanitize_context,
)
# Mantenha as outras importações que já estavam lá!

logger = logging.getLogger(__name__)

DISCLAIMER_PACIENTE = (
    "Conteúdo de apoio. Não substitui bula/protocolos e orientação profissional."
)

@login_required(login_url='/login/')
@role_required("MEDICO", "GESTOR", "ADMIN")
def atendimento_medico(request):
    user_hospital = get_user_hospital(request.user)
    pacientes = Paciente.objects.all()
    if request.user.tipo in ("MEDICO", "GESTOR"):
        if not user_hospital:
            raise PermissionDenied
        pacientes = Paciente.objects.for_user(request.user)
    
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
            paciente_qs = Paciente.objects.filter(id=request.POST.get('paciente'))
            if request.user.tipo in ("MEDICO", "GESTOR"):
                paciente_qs = paciente_qs.filter(hospital=user_hospital)
            paciente_selecionado = paciente_qs.first()
        elif consulta_id:
            try:
                consulta_temp = Consulta.objects.select_related("paciente").get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta_temp.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                paciente_selecionado = consulta_temp.paciente
            except (Consulta.DoesNotExist, PermissionDenied):
                paciente_selecionado = None
                messages.error(request, "Paciente não encontrado ou sem permissão.")

        # CENÁRIO A: SALVAR EDIÇÃO MANUAL
        if acao == 'salvar_edicao':
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                if not consulta.hospital_id:
                    consulta.hospital = consulta.paciente.hospital
                consulta.prescricao = request.POST.get('receita_editavel')
                consulta.save()
                
                # Recarrega dados
                analise_tecnica = consulta.analise_ia
                receita_paciente = consulta.prescricao
                historico_conversa = consulta.sintomas

        # CENÁRIO A.2: FINALIZAR/ASSINAR
        elif acao == 'finalizar_receita':
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                checks = [
                    request.POST.get("confirmacao_1"),
                    request.POST.get("confirmacao_2"),
                    request.POST.get("confirmacao_3"),
                    request.POST.get("confirmacao_4"),
                ]
                if not all(checks):
                    messages.error(request, "Confirme todos os itens antes de assinar.")
                else:
                    receita = consulta.receitas.order_by("-version").first()
                    if receita:
                        receita.status = Receita.STATUS_ASSINADA
                        receita.save(update_fields=["status"])
                        AuditLog.objects.create(
                            user=request.user,
                            hospital=consulta.hospital,
                            action="ASSINATURA_ACEITE_IA",
                            object_type="Receita",
                            object_id=str(receita.id),
                        )
                        messages.success(request, "Receita assinada com sucesso.")
                    else:
                        messages.error(request, "Nenhum rascunho encontrado para assinar.")

        # CENÁRIO B: GERAR COM IA (RASCUNHO)
        elif acao == 'gerar_ia':
            sintomas = request.POST.get('sintomas')
            historico_anterior = request.POST.get('historico_conversa', '')
            
            try:
                conversa_atual = f"{historico_anterior}\nMédico: {sintomas}"
                contexto_clinico = {
                    "sintomas": sintomas,
                    "historico": historico_anterior,
                }
                contexto_sem_pii = sanitize_context(contexto_clinico)
                rascunho = generate_prescription(contexto_sem_pii)
                resumo_tecnico = rascunho.get("resumo_tecnico_medico", [])
                if isinstance(resumo_tecnico, str):
                    resumo_tecnico = [resumo_tecnico]
                analise_tecnica = "\n".join(resumo_tecnico)
                medicamentos = []
                for med in rascunho.get("medicamentos", []):
                    medicamentos.append(
                        f"- {med['nome']} ({med['principio_ativo']}), {med['forma']} {med['concentracao']} | "
                        f"{med['posologia']} | {med['via']} | {med['frequencia']} | {med['duracao']}"
                    )
                receita_paciente = "\n".join(
                    medicamentos
                    + rascunho.get("orientacoes_ao_paciente", [])
                    + rascunho.get("alertas_seguranca", [])
                )
                receita_paciente = f"{receita_paciente}\n\n{DISCLAIMER_PACIENTE}"

                historico_conversa = f"{conversa_atual}\nIA: rascunho estruturado gerado."

                # Salva no banco
                if consulta_id:
                    consulta = Consulta.objects.get(id=consulta_id)
                    if request.user.tipo in ("MEDICO", "GESTOR"):
                        if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                            raise PermissionDenied
                    consulta.hospital = consulta.paciente.hospital
                    consulta.sintomas = historico_conversa
                    consulta.analise_ia = analise_tecnica
                    consulta.prescricao = receita_paciente
                    consulta.save()
                else:
                    nova_consulta = Consulta.objects.create(
                        paciente=paciente_selecionado,
                        medico=request.user,
                        hospital=user_hospital or paciente_selecionado.hospital,
                        sintomas=historico_conversa,
                        analise_ia=analise_tecnica,
                        prescricao=receita_paciente
                    )
                    consulta_id = nova_consulta.id
                    consulta = nova_consulta

                Receita.objects.create(
                    consulta=consulta,
                    hospital=consulta.hospital,
                    version=consulta.receitas.count() + 1,
                    status=Receita.STATUS_RASCUNHO,
                    json_content=rascunho,
                    created_by=request.user,
                )
                AiDraft.objects.create(
                    hospital=consulta.hospital,
                    consulta=consulta,
                    input_sem_pii=contexto_sem_pii,
                    output_json=rascunho,
                    modelo="gpt-4o-mini",
                    prompt_version=1,
                )
                AuditLog.objects.create(
                    user=request.user,
                    hospital=consulta.hospital,
                    action="gerar_rascunho_receita",
                    object_type="Consulta",
                    object_id=str(consulta.id),
                )

            except OpenAIPrescriptionError:
                analise_tecnica = "Falha ao gerar análise."
                receita_paciente = "Não foi possível gerar o rascunho agora. Tente novamente."
            except PermissionDenied:
                messages.error(request, "Acesso negado.")
            except Exception:
                logger.exception("Erro inesperado ao gerar receita.")
                analise_tecnica = "Falha inesperada ao gerar análise."
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
@role_required("MEDICO", "GESTOR", "ADMIN")
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required(login_url='/login/')
@role_required("MEDICO", "GESTOR", "ADMIN")
@hospital_scope_required(model=Consulta, lookup_kwarg="consulta_id")
def gerar_receita(request, consulta_id):
    consulta = request._scoped_object
    return render(request, 'receita.html', {'consulta': consulta})

@login_required(login_url='/login/')
@role_required("GESTOR", "ADMIN")
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
            User = get_user_model()
            if User.objects.filter(username=data['nome_usuario']).exists():
                messages.error(request, "Este nome de usuário já existe.")
            else:
                # Cria o Usuário (Login)
                novo_user = User.objects.create_user(
                    username=data['nome_usuario'],
                    email=data['email'],
                    password=data['senha'],
                    tipo="MEDICO",
                    hospital=hospital,
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
@role_required("MEDICO", "ADMIN")
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


@login_required(login_url='/login/')
@role_required("ADMIN")
def convidar_medico(request):
    hospital_queryset = Hospital.objects.all()
    if request.method == "POST":
        form = ConviteMedicoForm(request.POST, hospital_queryset=hospital_queryset)
        if form.is_valid():
            data = form.cleaned_data
            User = get_user_model()
            user = User.objects.create_user(
                username=data["nome_usuario"],
                email=data["email"],
                password=None,
                tipo="MEDICO",
                hospital=data["hospital"],
                is_active=False,
            )
            PerfilMedico.objects.create(
                usuario=user,
                hospital=data["hospital"],
                crm=data["crm"],
            )

            token_generator = PasswordResetTokenGenerator()
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = token_generator.make_token(user)
            link = request.build_absolute_uri(
                reverse("aceitar_convite", kwargs={"uidb64": uid, "token": token})
            )
            message = render_to_string(
                "email/convite_medico.txt",
                {"link": link, "user": user},
            )
            send_mail(
                "Convite PrescrittoMED - Defina sua senha",
                message,
                None,
                [user.email],
            )
            AuditLog.objects.create(
                user=request.user,
                hospital=data["hospital"],
                action="convidar_medico",
                object_type="Usuario",
                object_id=str(user.id),
            )
            messages.success(request, "Convite enviado com sucesso.")
            return redirect("convidar_medico")
    else:
        form = ConviteMedicoForm(hospital_queryset=hospital_queryset)

    return render(request, "convite_medico.html", {"form": form})


def aceitar_convite(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        User = get_user_model()
        user = User.objects.get(pk=uid)
    except (ValueError, User.DoesNotExist):
        user = None

    token_generator = PasswordResetTokenGenerator()
    if not user or not token_generator.check_token(user, token):
        messages.error(request, "Link inválido ou expirado.")
        return redirect("login")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.is_active = True
            user.save(update_fields=["is_active"])
            auth_login(request, user)
            messages.success(request, "Senha definida com sucesso.")
            return redirect("dashboard")
    else:
        form = SetPasswordForm(user)

    return render(request, "convite_set_password.html", {"form": form})
