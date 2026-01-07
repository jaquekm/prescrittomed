from django.contrib import admin
from django.urls import path
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from core.views import atendimento_medico, dashboard, gerar_receita, gestao_hospital, perfil_medico

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

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)