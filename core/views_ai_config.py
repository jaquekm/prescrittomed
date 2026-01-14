from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import HospitalKnowledgeForm, IAConfigForm
from .models import AiFeedback, HospitalConfig, HospitalKnowledgeItem, PromptTemplate
from .permissions import get_user_hospital, role_required


@login_required(login_url="/login/")
@role_required("ADMIN", "GESTOR")
def ia_config(request):
    hospital = get_user_hospital(request.user)
    if not hospital:
        messages.error(request, "Hospital não encontrado.")
        return redirect("dashboard")
    prompt = PromptTemplate.objects.filter(hospital=hospital, ativo=True).order_by("-versao").first()
    config, _ = HospitalConfig.objects.get_or_create(hospital=hospital)

    if request.method == "POST":
        if request.POST.get("acao") == "novo_conhecimento":
            conhecimento_form = HospitalKnowledgeForm(request.POST)
            form = IAConfigForm(initial={"prompt_template": prompt.conteudo if prompt else ""})
            if conhecimento_form.is_valid():
                HospitalKnowledgeItem.objects.create(
                    hospital=hospital,
                    tipo=conhecimento_form.cleaned_data["tipo"],
                    texto=conhecimento_form.cleaned_data["texto"],
                    aprovado_por=request.user,
                )
                messages.success(request, "Conteúdo adicionado à biblioteca.")
                return redirect("ia_config")
        else:
            form = IAConfigForm(request.POST)
            conhecimento_form = HospitalKnowledgeForm()
            if form.is_valid():
                conteudo = form.cleaned_data["prompt_template"]
                nova_versao = (prompt.versao if prompt else 0) + 1
                PromptTemplate.objects.create(hospital=hospital, versao=nova_versao, conteudo=conteudo, ativo=True)
                if prompt:
                    prompt.ativo = False
                    prompt.save(update_fields=["ativo"])
                config.estilo_orientacao = form.cleaned_data.get("estilo_orientacao", "")
                config.defaults_orientacao = form.cleaned_data.get("defaults_orientacao", "")
                config.save(update_fields=["estilo_orientacao", "defaults_orientacao"])
                messages.success(request, "Template atualizado.")
                return redirect("ia_config")
    else:
        form = IAConfigForm(
            initial={
                "prompt_template": prompt.conteudo if prompt else "",
                "estilo_orientacao": config.estilo_orientacao,
                "defaults_orientacao": config.defaults_orientacao,
            }
        )
        conhecimento_form = HospitalKnowledgeForm()

    conhecimento = HospitalKnowledgeItem.objects.filter(hospital=hospital).order_by("-created_at")
    feedbacks = AiFeedback.objects.filter(hospital=hospital).select_related("medico").order_by("-created_at")

    return render(
        request,
        "ia_config.html",
        {
            "form": form,
            "prompt": prompt,
            "conhecimento_form": conhecimento_form,
            "conhecimento": conhecimento,
            "feedbacks": feedbacks,
        },
    )
