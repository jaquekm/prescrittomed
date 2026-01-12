from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render

from .models import AuditLog, Consulta, Receita
from .permissions import get_user_hospital, role_required


@login_required(login_url="/login/")
@role_required("MEDICO", "GESTOR", "ADMIN")
def revisar_receita(request, consulta_id):
    consulta = Consulta.objects.get(pk=consulta_id)
    hospital = get_user_hospital(request.user)
    if not hospital or consulta.hospital_id != hospital.id:
        raise PermissionDenied

    receita = consulta.receitas.order_by("-version").first()

    if request.method == "POST":
        acao = request.POST.get("acao")
        if acao == "salvar_revisao":
            consulta.prescricao = request.POST.get("prescricao", "")
            consulta.status = Consulta.STATUS_EM_REVISAO
            consulta.save(update_fields=["prescricao", "status"])
            messages.success(request, "Revisão salva com sucesso.")
            return redirect("revisar_receita", consulta_id=consulta.id)
        if acao == "assinar_revisao":
            if consulta.status != Consulta.STATUS_EM_REVISAO:
                messages.error(request, "Finalize somente após revisar a receita.")
                return redirect("revisar_receita", consulta_id=consulta.id)
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
                object_id=str(receita.id if receita else consulta.id),
            )
            messages.success(request, "Receita assinada com sucesso.")
            return redirect("gerar_receita", consulta_id=consulta.id)
    elif consulta.status == Consulta.STATUS_RASCUNHO_SALVO:
        consulta.status = Consulta.STATUS_EM_REVISAO
        consulta.save(update_fields=["status"])

    return render(
        request,
        "receita_revisao.html",
        {
            "consulta": consulta,
            "receita": receita,
        },
    )
