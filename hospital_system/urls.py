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
from core.views_ai import teste_openai
from core.views_health import health, ready

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Login e Logout
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Sistema Principal
    path('', dashboard, name='dashboard'),
    path('atendimento/', atendimento_medico, name='atendimento'),
    path('receita/<int:consulta_id>/', gerar_receita, name='gerar_receita'),
    
    # Novas Rotas de Gestão
    path('gestao/', gestao_hospital, name='gestao_hospital'),
    path('perfil/', perfil_medico, name='perfil_medico'),
    path('convites/medicos/', convidar_medico, name='convidar_medico'),
    path('convites/aceitar/<uidb64>/<token>/', aceitar_convite, name='aceitar_convite'),
    path('health/', health, name='health'),
    path('ready/', ready, name='ready'),
    path('ai/teste/', teste_openai, name='teste_openai'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
