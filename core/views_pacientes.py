from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import ObservacaoForm, PacienteForm
from .models import Consulta, Observacao, Paciente, Receita
from .permissions import get_user_hospital, role_required


def _pacientes_visiveis(user):
    hospital = get_user_hospital(user)
    if not hospital:
        return Paciente.objects.none()
    queryset = Paciente.objects.filter(hospital=hospital)
    if user.tipo == "MEDICO" and not user.pode_ver_todos_pacientes:
        queryset = queryset.filter(Q(medico_responsavel=user) | Q(consulta__medico=user)).distinct()
    return queryset


@login_required(login_url="/login/")
@role_required("MEDICO", "GESTOR", "ADMIN")
def pacientes_lista(request):
    busca = request.GET.get("busca", "")
    pacientes = _pacientes_visiveis(request.user)
    if busca:
        pacientes = pacientes.filter(Q(nome_completo__icontains=busca) | Q(cpf__icontains=busca))

    return render(
        request,
        "pacientes_lista.html",
        {"pacientes": pacientes, "busca": busca, "cta_url": reverse("paciente_criar")},
    )


@login_required(login_url="/login/")
@role_required("MEDICO", "GESTOR", "ADMIN")
def paciente_criar(request):
    hospital = get_user_hospital(request.user)
    if not hospital:
        raise PermissionDenied

    if request.method == "POST":
        form = PacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.hospital = hospital
            if request.user.tipo == "MEDICO" and not request.user.pode_ver_todos_pacientes:
                paciente.medico_responsavel = request.user
            paciente.save()
            messages.success(request, "Paciente cadastrado com sucesso.")
            return redirect("paciente_detalhe", paciente_id=paciente.id)
    else:
        form = PacienteForm()

    return render(request, "paciente_form.html", {"form": form, "titulo": "Novo paciente"})


@login_required(login_url="/login/")
@role_required("MEDICO", "GESTOR", "ADMIN")
def paciente_editar(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    if paciente not in _pacientes_visiveis(request.user):
        raise PermissionDenied

    if request.method == "POST":
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            form.save()
            messages.success(request, "Paciente atualizado com sucesso.")
            return redirect("paciente_detalhe", paciente_id=paciente.id)
    else:
        form = PacienteForm(instance=paciente)

    return render(request, "paciente_form.html", {"form": form, "titulo": "Editar paciente"})


@login_required(login_url="/login/")
@role_required("MEDICO", "GESTOR", "ADMIN")
def paciente_detalhe(request, paciente_id):
    paciente = get_object_or_404(Paciente, pk=paciente_id)
    if paciente not in _pacientes_visiveis(request.user):
        raise PermissionDenied

    consultas = Consulta.objects.filter(paciente=paciente).order_by("-data")
    receitas = Receita.objects.filter(consulta__paciente=paciente).order_by("-created_at")
    observacoes = Observacao.objects.filter(consulta__paciente=paciente).order_by("-created_at")

    if request.method == "POST":
        form = ObservacaoForm(request.POST)
        if form.is_valid():
            consulta_ref = consultas.first()
            if not consulta_ref:
                messages.error(request, "Cadastre uma consulta antes de adicionar observações.")
            else:
                Observacao.objects.create(
                    consulta=consulta_ref,
                    hospital=paciente.hospital,
                    texto=form.cleaned_data["texto"],
                    created_by=request.user,
                )
                messages.success(request, "Observação adicionada.")
                return redirect("paciente_detalhe", paciente_id=paciente.id)
    else:
        form = ObservacaoForm()

    return render(
        request,
        "paciente_detalhe.html",
        {
            "paciente": paciente,
            "consultas": consultas,
            "receitas": receitas,
            "observacoes": observacoes,
            "form": form,
        },
    )
