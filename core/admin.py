from django.contrib import admin
from .models import Hospital, PerfilMedico, Paciente, Consulta

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