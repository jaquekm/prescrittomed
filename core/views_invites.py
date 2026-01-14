from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from .models import MedicoInvite
from .permissions import get_user_hospital, role_required


@login_required(login_url="/login/")
@role_required("ADMIN", "GESTOR")
def convites_lista(request):
    hospital = get_user_hospital(request.user)
    if not hospital:
        messages.error(request, "Hospital não encontrado.")
        return redirect("dashboard")
    invites = MedicoInvite.objects.filter(hospital=hospital).select_related("user").order_by("-created_at")
    agora = timezone.now()
    expirados = invites.filter(status=MedicoInvite.STATUS_PENDENTE, expires_at__lt=agora)
    if expirados.exists():
        expirados.update(status=MedicoInvite.STATUS_EXPIRADO)

    return render(
        request,
        "convites_lista.html",
        {"invites": invites, "cta_url": reverse("convidar_medico")},
    )


@login_required(login_url="/login/")
@role_required("ADMIN", "GESTOR")
def reenviar_convite(request, invite_id):
    hospital = get_user_hospital(request.user)
    invite = MedicoInvite.objects.filter(hospital=hospital, pk=invite_id).select_related("user").first()
    if not invite:
        messages.error(request, "Convite não encontrado.")
        return redirect("convites_lista")

    user = invite.user
    token_generator = PasswordResetTokenGenerator()
    token = token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    link = request.build_absolute_uri(
        reverse("aceitar_convite", kwargs={"uidb64": uid, "token": token})
    )
    invite.token = token
    invite.status = MedicoInvite.STATUS_PENDENTE
    invite.expires_at = timezone.now() + timezone.timedelta(days=7)
    invite.save(update_fields=["token", "status", "expires_at"])

    message = render_to_string("email/convite_medico.txt", {"link": link, "user": user})
    send_mail(
        "Convite PrescrittoMED - Defina sua senha",
        message,
        None,
        [user.email],
    )

    messages.success(request, "Convite reenviado com sucesso.")
    return redirect("convites_lista")
