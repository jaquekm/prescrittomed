from django import forms
from .models import Hospital, PerfilMedico

class NovoMedicoForm(forms.Form):
    nome_usuario = forms.CharField(label="Nome de Usuário (Login)", max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    senha = forms.CharField(label="Senha Inicial", widget=forms.PasswordInput)
    crm = forms.CharField(label="CRM", max_length=20)

class ConviteMedicoForm(forms.Form):
    nome_usuario = forms.CharField(label="Nome de Usuário (Login)", max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    crm = forms.CharField(label="CRM", max_length=20)
    hospital = forms.ModelChoiceField(label="Hospital", queryset=Hospital.objects.none())

    def __init__(self, *args, **kwargs):
        hospital_queryset = kwargs.pop("hospital_queryset", None)
        super().__init__(*args, **kwargs)
        if hospital_queryset is not None:
            self.fields["hospital"].queryset = hospital_queryset

class PerfilMedicoForm(forms.ModelForm):
    class Meta:
        model = PerfilMedico
        fields = ['crm', 'uf_crm', 'assinatura_img']
        labels = {
            'assinatura_img': 'Foto da Assinatura (Fundo branco)',
            'uf_crm': 'Estado (UF)'
        }
