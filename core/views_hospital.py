from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import HospitalBrandingForm, HospitalConfigForm, HospitalSignupForm
from .models import Hospital, HospitalConfig
from .permissions import get_user_hospital, role_required


@transaction.atomic
def hospital_onboarding(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    if request.method == "POST":
        form = HospitalSignupForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            User = get_user_model()
            if User.objects.filter(email=data["admin_email"]).exists():
                messages.error(request, "Já existe um usuário com este e-mail.")
            else:
                admin_user = User.objects.create_user(
                    username=data["admin_email"],
                    email=data["admin_email"],
                    password=data["admin_senha"],
                    tipo="ADMIN",
                    pode_ver_todos_pacientes=True,
                )
                hospital = Hospital.objects.create(
                    nome=data["nome_hospital"],
                    cnpj=data["cnpj"],
                    endereco=data["endereco"],
                    logo=data.get("logo"),
                    cor_primaria=data.get("cor_primaria") or "#2c3e50",
                    admin_responsavel=admin_user,
                )
                admin_user.hospital = hospital
                admin_user.save(update_fields=["hospital"])
                HospitalConfig.objects.create(hospital=hospital)
                messages.success(request, "Hospital cadastrado com sucesso. Faça login para continuar.")
                return redirect("login")
    else:
        form = HospitalSignupForm()

    return render(request, "hospital_signup.html", {"form": form})


@login_required(login_url="/login/")
@role_required("ADMIN", "GESTOR")
def hospital_settings(request):
    hospital = get_user_hospital(request.user)
    if not hospital:
        messages.error(request, "Hospital não encontrado.")
        return redirect("dashboard")

    config, _ = HospitalConfig.objects.get_or_create(hospital=hospital)

    if request.method == "POST":
        branding_form = HospitalBrandingForm(request.POST, request.FILES, instance=hospital)
        config_form = HospitalConfigForm(request.POST, instance=config)
        if branding_form.is_valid() and config_form.is_valid():
            branding_form.save()
            config_form.save()
            messages.success(request, "Configurações atualizadas com sucesso.")
            return redirect("hospital_settings")
    else:
        branding_form = HospitalBrandingForm(instance=hospital)
        config_form = HospitalConfigForm(instance=config)

    return render(
        request,
        "hospital_settings.html",
        {"branding_form": branding_form, "config_form": config_form},
    )
