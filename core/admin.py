from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .models import (
    AiDraft,
    AiFeedback,
    AuditLog,
    BulaAccessLog,
    BulaCache,
    Consulta,
    Hospital,
    HospitalKnowledgeItem,
    Observacao,
    Paciente,
    PerfilMedico,
    PromptTemplate,
    Receita,
)

# Configura como o Hospital aparece na lista
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cnpj', 'admin_responsavel')
    search_fields = ('nome',)

# Configura como o Médico aparece na lista
class PerfilMedicoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'crm', 'hospital')
    list_filter = ('hospital',)

admin.site.register(Hospital, HospitalAdmin)
admin.site.register(PerfilMedico, PerfilMedicoAdmin)
admin.site.register(Paciente)
admin.site.register(Consulta)
admin.site.register(Receita)
admin.site.register(Observacao)
admin.site.register(AuditLog)
admin.site.register(PromptTemplate)
admin.site.register(HospitalKnowledgeItem)
admin.site.register(AiDraft)
admin.site.register(AiFeedback)
admin.site.register(BulaCache)
admin.site.register(BulaAccessLog)

User = get_user_model()


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "email", "tipo", "hospital", "is_staff")
    list_filter = ("tipo", "hospital", "is_staff", "is_superuser")
    search_fields = ("username", "email", "crm")
    fieldsets = UserAdmin.fieldsets + (
        ("Perfil", {"fields": ("tipo", "crm", "hospital")}),
    )
