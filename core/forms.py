from django import forms
from django.contrib.auth.models import User
from .models import PerfilMedico

class NovoMedicoForm(forms.Form):
    nome_usuario = forms.CharField(label="Nome de Usuário (Login)", max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    senha = forms.CharField(label="Senha Inicial", widget=forms.PasswordInput)
    crm = forms.CharField(label="CRM", max_length=20)

class PerfilMedicoForm(forms.ModelForm):
    class Meta:
        model = PerfilMedico
        fields = ['crm', 'uf_crm', 'assinatura_img']
        labels = {
            'assinatura_img': 'Foto da Assinatura (Fundo branco)',
            'uf_crm': 'Estado (UF)'
        }