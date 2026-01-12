from django import forms
from .models import Hospital, HospitalConfig, PerfilMedico, Paciente

class BootstrapFormMixin:
    def _apply_bootstrap(self):
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                existing = widget.attrs.get("class", "")
                widget.attrs["class"] = f"{existing} form-check-input".strip()
                continue
            if isinstance(widget, forms.RadioSelect):
                continue
            existing = widget.attrs.get("class", "")
            widget.attrs["class"] = f"{existing} form-control".strip()


class NovoMedicoForm(BootstrapFormMixin, forms.Form):
    TIPO_CHOICES = (
        ("MEDICO", "Médico"),
        ("GESTOR", "Gestor"),
    )

    nome_usuario = forms.CharField(label="Nome de Usuário (Login)", max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    senha = forms.CharField(label="Senha Inicial", widget=forms.PasswordInput)
    crm = forms.CharField(label="CRM", max_length=20)
    tipo = forms.ChoiceField(label="Tipo de acesso", choices=TIPO_CHOICES)
    pode_ver_todos_pacientes = forms.BooleanField(
        label="Pode ver todos os pacientes do hospital",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()

class ConviteMedicoForm(BootstrapFormMixin, forms.Form):
    TIPO_CHOICES = (
        ("MEDICO", "Médico"),
        ("GESTOR", "Gestor"),
    )

    nome_usuario = forms.CharField(label="Nome de Usuário (Login)", max_length=150)
    email = forms.EmailField(label="E-mail", required=True)
    crm = forms.CharField(label="CRM", max_length=20)
    tipo = forms.ChoiceField(label="Tipo de acesso", choices=TIPO_CHOICES)
    pode_ver_todos_pacientes = forms.BooleanField(
        label="Pode ver todos os pacientes do hospital",
        required=False,
    )
    hospital = forms.ModelChoiceField(label="Hospital", queryset=Hospital.objects.none())

    def __init__(self, *args, **kwargs):
        hospital_queryset = kwargs.pop("hospital_queryset", None)
        super().__init__(*args, **kwargs)
        if hospital_queryset is not None:
            self.fields["hospital"].queryset = hospital_queryset
        self._apply_bootstrap()

class PerfilMedicoForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = PerfilMedico
        fields = ['crm', 'uf_crm', 'assinatura_img']
        labels = {
            'assinatura_img': 'Foto da Assinatura (Fundo branco)',
            'uf_crm': 'Estado (UF)'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class HospitalSignupForm(BootstrapFormMixin, forms.Form):
    nome_hospital = forms.CharField(label="Nome do Hospital", max_length=100)
    cnpj = forms.CharField(label="CNPJ", max_length=20)
    endereco = forms.CharField(label="Endereço", widget=forms.Textarea(attrs={"rows": 3}))
    cor_primaria = forms.CharField(label="Cor primária (hex)", max_length=7, required=False)
    logo = forms.ImageField(label="Logo do hospital (opcional)", required=False)
    admin_nome = forms.CharField(label="Nome do administrador", max_length=150)
    admin_email = forms.EmailField(label="E-mail do administrador")
    admin_senha = forms.CharField(label="Senha", widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class HospitalConfigForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = HospitalConfig
        fields = [
            "dominios_permitidos",
            "modo_privacidade",
            "retencao_dados_dias",
            "assinatura_rodape",
            "estilo_orientacao",
            "defaults_orientacao",
        ]
        labels = {
            "dominios_permitidos": "Domínios/hosts permitidos",
            "modo_privacidade": "Modo privacidade",
            "retencao_dados_dias": "Retenção de dados (dias)",
            "assinatura_rodape": "Assinatura/rodapé",
            "estilo_orientacao": "Estilo do texto ao paciente",
            "defaults_orientacao": "Defaults de orientação",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class HospitalBrandingForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Hospital
        fields = ["nome", "cnpj", "endereco", "logo", "cor_primaria"]
        labels = {
            "nome": "Nome do hospital",
            "cnpj": "CNPJ",
            "endereco": "Endereço",
            "logo": "Logo",
            "cor_primaria": "Cor primária",
        }
        widgets = {
            "endereco": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class PacienteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Paciente
        fields = ["nome_completo", "data_nascimento", "cpf", "historico_alergias"]
        labels = {
            "nome_completo": "Nome completo",
            "data_nascimento": "Data de nascimento",
            "historico_alergias": "Alergias",
        }
        widgets = {
            "data_nascimento": forms.DateInput(attrs={"type": "date"}),
            "historico_alergias": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class ObservacaoForm(BootstrapFormMixin, forms.Form):
    texto = forms.CharField(label="Observação clínica", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class IAConfigForm(BootstrapFormMixin, forms.Form):
    prompt_template = forms.CharField(label="Prompt template ativo", widget=forms.Textarea(attrs={"rows": 4}))
    estilo_orientacao = forms.CharField(label="Estilo do texto ao paciente", widget=forms.Textarea(attrs={"rows": 3}), required=False)
    defaults_orientacao = forms.CharField(label="Defaults de orientação", widget=forms.Textarea(attrs={"rows": 3}), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()


class HospitalKnowledgeForm(BootstrapFormMixin, forms.Form):
    tipo = forms.CharField(label="Tipo de conteúdo", max_length=100)
    texto = forms.CharField(label="Conteúdo aprovado", widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_bootstrap()
