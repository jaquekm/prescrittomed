from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core.views import (
    aceitar_convite,
    atendimento_medico,
    convidar_medico,
    dashboard,
    gerar_receita,
    gestao_hospital,
    perfil_medico,
)
from core.views_hospital import hospital_onboarding, hospital_settings
from core.views_invites import convites_lista, reenviar_convite
from core.views_pacientes import paciente_criar, paciente_detalhe, paciente_editar, pacientes_lista
from core.views_receita import revisar_receita
from core.views_ai_config import ia_config
from core.views_ai import teste_openai
from core.views_health import health, ready

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login e Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('onboarding/', hospital_onboarding, name='hospital_onboarding'),
    
    # Sistema Principal
    path('', dashboard, name='dashboard'),
    path('atendimento/', atendimento_medico, name='atendimento'),
    path('receita/<int:consulta_id>/', gerar_receita, name='gerar_receita'),
    path('receita/<int:consulta_id>/revisao/', revisar_receita, name='revisar_receita'),
    
    # Novas Rotas de Gestão
    path('gestao/', gestao_hospital, name='gestao_hospital'),
    path('perfil/', perfil_medico, name='perfil_medico'),
    path('convites/medicos/', convidar_medico, name='convidar_medico'),
    path('convites/', convites_lista, name='convites_lista'),
    path('convites/reenviar/<int:invite_id>/', reenviar_convite, name='reenviar_convite'),
    path('convites/aceitar/<uidb64>/<token>/', aceitar_convite, name='aceitar_convite'),
    path('hospital/configuracoes/', hospital_settings, name='hospital_settings'),
    path('ia/config/', ia_config, name='ia_config'),
    path('pacientes/', pacientes_lista, name='pacientes_lista'),
    path('pacientes/novo/', paciente_criar, name='paciente_criar'),
    path('pacientes/<int:paciente_id>/', paciente_detalhe, name='paciente_detalhe'),
    path('pacientes/<int:paciente_id>/editar/', paciente_editar, name='paciente_editar'),
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('ai/teste/', teste_openai, name='teste_openai'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
