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

class AuditLogAdmin(admin.ModelAdmin):
    """Admin configurado para facilitar auditorias de compliance"""
    list_display = (
        'id', 
        'action', 
        'user', 
        'hospital', 
        'consulta', 
        'timestamp',
        'lgpd_compliant',
        'anvisa_compliant'
    )
    list_filter = (
        'action', 
        'hospital', 
        'timestamp', 
        'lgpd_compliant', 
        'anvisa_compliant',
        'modelo_ia'
    )
    search_fields = (
        'user__username', 
        'user__email', 
        'consulta__id', 
        'receita__id',
        'ip_address'
    )
    readonly_fields = (
        'timestamp',
        'pdf_generated_at',
        'lgpd_compliant',
        'anvisa_compliant'
    )
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('user', 'hospital', 'action', 'timestamp')
        }),
        ('Relacionamentos', {
            'fields': ('consulta', 'receita')
        }),
        ('Dados de Entrada (Sanitizados)', {
            'fields': ('input_data',),
            'description': 'Dados de entrada sem PII conforme LGPD'
        }),
        ('Sugestão da IA', {
            'fields': (
                'ai_suggestion',
                'source_ids_used',
                'confidence_score',
                'modelo_ia',
                'prompt_version'
            )
        }),
        ('Edições do Médico', {
            'fields': (
                'doctor_edit',
                'manual_override_reason',
                'break_glass_confirmed'
            )
        }),
        ('Prescrição Final', {
            'fields': ('final_prescription',)
        }),
        ('PDF Gerado', {
            'fields': ('pdf_hash', 'pdf_generated_at')
        }),
        ('Rastreabilidade', {
            'fields': ('ip_address', 'user_agent', 'session_id')
        }),
        ('Compliance', {
            'fields': ('lgpd_compliant', 'anvisa_compliant')
        }),
    )
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

admin.site.register(Hospital, HospitalAdmin)
admin.site.register(PerfilMedico, PerfilMedicoAdmin)
admin.site.register(Paciente)
admin.site.register(Consulta)
admin.site.register(Receita)
admin.site.register(Observacao)
admin.site.register(AuditLog, AuditLogAdmin)
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
