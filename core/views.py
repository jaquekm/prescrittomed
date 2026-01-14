import logging

from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.exceptions import PermissionDenied
from django.db import models
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from django.utils import timezone

from .forms import ConviteMedicoForm, NovoMedicoForm, PerfilMedicoForm
from .models import (
    AiDraft,
    AuditLog,
    Consulta,
    Hospital,
    MedicoInvite,
    Paciente,
    PerfilMedico,
    Receita,
)
from .permissions import get_user_hospital, hospital_scope_required, role_required
from .services.bula_fetcher import BulaFetcherError, fetch_bula, summarize_bula
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
    if request.user.tipo in ("MEDICO", "GESTOR", "ADMIN"):
        if not user_hospital:
            raise PermissionDenied
        pacientes = Paciente.objects.filter(hospital=user_hospital)
        if request.user.tipo == "MEDICO" and not request.user.pode_ver_todos_pacientes:
            pacientes = pacientes.filter(
                models.Q(medico_responsavel=request.user) | models.Q(consulta__medico=request.user)
            ).distinct()
    
    # Variáveis iniciais
    analise_tecnica = ""
    receita_paciente = ""
    historico_conversa = ""
    paciente_selecionado = None
    consulta_id = request.POST.get('consulta_id')
    paciente_preselecionado = request.GET.get("paciente")

    bula_resultado = None
    bula_resumo = None

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
                consulta.status = Consulta.STATUS_RASCUNHO_SALVO
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
                if consulta.status != Consulta.STATUS_EM_REVISAO:
                    messages.error(request, "Finalize somente após revisar a receita.")
                elif not all(checks):
                    messages.error(request, "Confirme todos os itens antes de assinar.")
                else:
                    receita = consulta.receitas.order_by("-version").first()
                    if receita:
                        receita.status = Receita.STATUS_ASSINADA
                        receita.save(update_fields=["status"])
                        consulta.status = Consulta.STATUS_ASSINADA
                        consulta.save(update_fields=["status"])
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
                chat_messages = []
                if consulta_id:
                    chat_messages = Consulta.objects.filter(id=consulta_id).values_list("chat_messages", flat=True).first() or []
                chat_messages = list(chat_messages) + [
                    {"role": "user", "content": sintomas},
                    {"role": "assistant", "content": analise_tecnica},
                ]

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
                    consulta.status = Consulta.STATUS_RASCUNHO_SALVO
                    consulta.chat_messages = chat_messages
                    consulta.save()
                else:
                    nova_consulta = Consulta.objects.create(
                        paciente=paciente_selecionado,
                        medico=request.user,
                        hospital=user_hospital or paciente_selecionado.hospital,
                        sintomas=historico_conversa,
                        analise_ia=analise_tecnica,
                        prescricao=receita_paciente,
                        status=Consulta.STATUS_RASCUNHO_SALVO,
                        chat_messages=chat_messages,
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

        elif acao == "aplicar_rascunho":
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                consulta.prescricao = request.POST.get("receita_rascunho", "")
                consulta.status = Consulta.STATUS_RASCUNHO_SALVO
                consulta.save(update_fields=["prescricao", "status"])
                messages.success(request, "Rascunho aplicado na receita.")

        elif acao == "avancar_revisao":
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                consulta.status = Consulta.STATUS_EM_REVISAO
                consulta.save(update_fields=["status"])
                return redirect("revisar_receita", consulta_id=consulta.id)

        elif acao == "buscar_bula":
            termo_bula = request.POST.get("termo_bula", "")
            if termo_bula:
                try:
                    bula_resultado = fetch_bula(termo_bula, user_hospital)
                    if request.POST.get("gerar_resumo") == "1":
                        bula_resumo = summarize_bula(bula_resultado.get("conteudo", ""))
                except BulaFetcherError as exc:
                    messages.error(request, str(exc))
            else:
                messages.error(request, "Informe um termo para buscar a bula.")
        elif acao == "aplicar_bula":
            if consulta_id:
                consulta = Consulta.objects.get(id=consulta_id)
                if request.user.tipo in ("MEDICO", "GESTOR"):
                    if not user_hospital or consulta.paciente.hospital_id != user_hospital.id:
                        raise PermissionDenied
                bula_texto = request.POST.get("bula_resumo", "")
                if bula_texto:
                    consulta.prescricao = f"{consulta.prescricao}\n\nOrientações da bula:\n{bula_texto}"
                    consulta.save(update_fields=["prescricao"])
                    messages.success(request, "Orientações adicionadas à receita.")

    if not request.method == "POST" and paciente_preselecionado:
        paciente_qs = Paciente.objects.filter(id=paciente_preselecionado)
        if request.user.tipo in ("MEDICO", "GESTOR") and user_hospital:
            paciente_qs = paciente_qs.filter(hospital=user_hospital)
        paciente_selecionado = paciente_qs.first()

    return render(request, 'atendimento.html', {
        'analise_tecnica': analise_tecnica,
        'receita_paciente': receita_paciente, # Vai para o editor
        'historico_conversa': historico_conversa,
        'pacientes': pacientes,
        'paciente_selecionado': paciente_selecionado,
        'consulta_id': consulta_id,
        'bula_resultado': bula_resultado,
        'bula_resumo': bula_resumo,
        'chat_messages': Consulta.objects.filter(id=consulta_id).values_list("chat_messages", flat=True).first() if consulta_id else [],
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
    config = getattr(consulta.hospital, "hospitalconfig", None)
    receita = consulta.receitas.order_by("-version").first()
    return render(request, 'receita.html', {'consulta': consulta, 'config': config, 'receita': receita})

@login_required(login_url='/login/')
@role_required("GESTOR", "ADMIN")
def gestao_hospital(request):
    hospital = get_user_hospital(request.user)
    if not hospital:
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
                    tipo=data["tipo"],
                    hospital=hospital,
                    pode_ver_todos_pacientes=data.get("pode_ver_todos_pacientes", False),
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
    user_hospital = get_user_hospital(request.user)
    if request.user.tipo in ("ADMIN", "GESTOR") and user_hospital:
        hospital_queryset = Hospital.objects.filter(id=user_hospital.id)
    else:
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
                tipo=data["tipo"],
                hospital=data["hospital"],
                is_active=False,
                pode_ver_todos_pacientes=data.get("pode_ver_todos_pacientes", False),
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
            expires_at = timezone.now() + timezone.timedelta(days=7)
            MedicoInvite.objects.create(
                user=user,
                hospital=data["hospital"],
                token=token,
                expires_at=expires_at,
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
    invite = MedicoInvite.objects.filter(user=user, token=token).order_by("-created_at").first()
    if invite and invite.expires_at < timezone.now():
        invite.status = MedicoInvite.STATUS_EXPIRADO
        invite.save(update_fields=["status"])
        messages.error(request, "Link expirado. Solicite um novo convite.")
        return redirect("login")

    if not user or not token_generator.check_token(user, token):
        messages.error(request, "Link inválido ou expirado.")
        return redirect("login")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            user.is_active = True
            user.save(update_fields=["is_active"])
            if invite:
                invite.status = MedicoInvite.STATUS_ACEITO
                invite.save(update_fields=["status"])
            AuditLog.objects.create(
                user=user,
                hospital=user.hospital,
                action="aceitar_convite",
                object_type="Usuario",
                object_id=str(user.id),
            )
            auth_login(request, user)
            messages.success(request, "Senha definida com sucesso.")
            return redirect("dashboard")
    else:
        form = SetPasswordForm(user)

    return render(request, "convite_set_password.html", {"form": form})
