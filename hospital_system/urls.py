from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

# Views do sistema (Django Templates)
from core.views import (
    aceitar_convite,
    atendimento_medico,
    convidar_medico,
    dashboard,
    gerar_receita,
    gestao_hospital,
    perfil_medico,
)

# Views da Inteligência (IA) e Utilitários
# ADICIONEI: prescribe_medication (para a IA funcionar)
from core.views_ai import teste_openai, prescribe_medication 

# ADICIONEI: gerar_receita_pdf (para o botão de imprimir funcionar)
from core.views_prescription import gerar_receita_pdf 

from core.views_health import health, ready

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login e Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Sistema Principal (Django Tradicional)
    path('', dashboard, name='dashboard'),
    path('atendimento/', atendimento_medico, name='atendimento'),
    path('receita/<int:consulta_id>/', gerar_receita, name='gerar_receita'),
    
    # Gestão
    path('gestao/', gestao_hospital, name='gestao_hospital'),
    path('perfil/', perfil_medico, name='perfil_medico'),
    path('convites/medicos/', convidar_medico, name='convidar_medico'),
    path('convites/aceitar/<uidb64>/<token>/', aceitar_convite, name='aceitar_convite'),
    
    # Utilitários
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('ai/teste/', teste_openai, name='teste_openai'),

    # --- API ENDPOINTS (Conexão com Next.js) ---
    # É aqui que a mágica acontece! 👇
    
    # 1. Rota para a IA analisar o caso
    path('api/v1/prescribe', prescribe_medication, name='api_prescribe'),

    # 2. Rota para gerar o PDF da receita
    path('api/v1/gerar-pdf', gerar_receita_pdf, name='api_gerar_pdf'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)