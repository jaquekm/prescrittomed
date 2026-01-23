from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .permissions import get_user_hospital


class HospitalScopedQuerySet(models.QuerySet):
    def for_user(self, user):
        hospital = get_user_hospital(user)
        if not hospital:
            return self.none()
        return self.filter(hospital=hospital)


class HospitalScopedManager(models.Manager):
    def get_queryset(self):
        return HospitalScopedQuerySet(self.model, using=self._db)

    def for_user(self, user):
        return self.get_queryset().for_user(user)

# 1. O HOSPITAL (Quem paga a conta)
class Hospital(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=20)
    endereco = models.TextField()
    # Novos campos de customização
    logo = models.ImageField(upload_to='logos_hospitais/', null=True, blank=True)
    cor_primaria = models.CharField(max_length=7, default='#2c3e50', help_text="Código Hex da cor (ex: #000000)")
    
    # O Administrador da conta desse hospital
    admin_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="hospitais_geridos",
    )

    def __str__(self):
        return self.nome

# 1.1 O USUÁRIO CUSTOMIZADO
class Usuario(AbstractUser):
    TIPO_CHOICES = (
        ("ADMIN", "Admin do Sistema"),
        ("GESTOR", "Gestor Hospitalar"),
        ("MEDICO", "Médico"),
    )

    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES, default="MEDICO")
    crm = models.CharField(max_length=20, blank=True, null=True)
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hospital", "email"], name="unique_email_por_hospital"),
        ]

# 2. O PERFIL DO MÉDICO (Extensão do Usuário)
class PerfilMedico(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil_medico',
    )
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE) # Médico pertence a um hospital
    crm = models.CharField(max_length=20)
    uf_crm = models.CharField(max_length=2, default='SP')
    # Assinatura digitalizada para sair na receita
    assinatura_img = models.ImageField(upload_to='assinaturas/', null=True, blank=True)
    
    def __str__(self):
        return f"Dr(a). {self.usuario.username} - CRM {self.crm}"

# 3. O PACIENTE
class Paciente(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE) # Paciente é do hospital, não do médico
    nome_completo = models.CharField(max_length=100)
    data_nascimento = models.DateField()
    cpf = models.CharField(max_length=14)
    historico_alergias = models.TextField(blank=True)
    
    def __str__(self):
        return self.nome_completo

    objects = HospitalScopedManager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["hospital", "cpf"], name="unique_cpf_por_hospital"),
        ]
        indexes = [
            models.Index(fields=["hospital"]),
        ]

# 4. A CONSULTA (Ligada ao histórico)
class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    sintomas = models.TextField() # Histórico do Chat
    analise_ia = models.TextField(null=True, blank=True) # Parte técnica
    prescricao = models.TextField(null=True, blank=True) # Receita final editada
    
    def __str__(self):
        return f"{self.paciente.nome_completo} - {self.data}"

    objects = HospitalScopedManager()

    class Meta:
        indexes = [
            models.Index(fields=["hospital"]),
        ]


class Receita(models.Model):
    STATUS_RASCUNHO = "RASCUNHO"
    STATUS_ASSINADA = "ASSINADA"
    STATUS_CHOICES = (
        (STATUS_RASCUNHO, "Rascunho"),
        (STATUS_ASSINADA, "Assinada"),
    )

    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name="receitas")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_RASCUNHO)
    json_content = models.JSONField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    def __str__(self):
        return f"Receita {self.consulta_id} v{self.version}"

    class Meta:
        indexes = [
            models.Index(fields=["hospital"]),
        ]


class Observacao(models.Model):
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, related_name="observacoes")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    texto = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    def __str__(self):
        return f"Observacao {self.consulta_id}"

    class Meta:
        indexes = [
            models.Index(fields=["hospital"]),
        ]


class AuditLog(models.Model):
    """
    Audit Trail completo para compliance ANVISA RDC 657/2022
    Registra imutavelmente todas as interações: Input, AI Suggestion, Doctor Edit, Final PDF
    """
    # Ações possíveis (conforme ActionType em schemas.py)
    ACTION_INPUT_RECEIVED = "INPUT_RECEIVED"
    ACTION_AI_SUGGESTION = "AI_SUGGESTION_GENERATED"
    ACTION_DOCTOR_EDIT = "DOCTOR_EDIT"
    ACTION_MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    ACTION_PRESCRIPTION_FINALIZED = "PRESCRIPTION_FINALIZED"
    ACTION_PDF_GENERATED = "PDF_GENERATED"
    ACTION_BREAK_GLASS = "BREAK_GLASS_CONFIRMATION"
    
    ACTION_CHOICES = (
        (ACTION_INPUT_RECEIVED, "Input Recebido"),
        (ACTION_AI_SUGGESTION, "Sugestão IA Gerada"),
        (ACTION_DOCTOR_EDIT, "Edição do Médico"),
        (ACTION_MANUAL_OVERRIDE, "Override Manual"),
        (ACTION_PRESCRIPTION_FINALIZED, "Prescrição Finalizada"),
        (ACTION_PDF_GENERATED, "PDF Gerado"),
        (ACTION_BREAK_GLASS, "Confirmação Break Glass"),
    )

    # Relacionamentos básicos
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="audit_logs")
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    
    # Relacionamentos opcionais com consulta/receita
    consulta = models.ForeignKey(
        Consulta, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name="audit_logs"
    )
    receita = models.ForeignKey(
        Receita,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs"
    )
    
    # Dados de entrada (sanitizados, sem PII)
    input_data = models.JSONField(null=True, blank=True, help_text="Dados de entrada sanitizados")
    
    # Sugestão da IA
    ai_suggestion = models.JSONField(null=True, blank=True, help_text="Sugestão completa da IA em JSON")
    source_ids_used = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Lista de source_ids das fontes consultadas pela IA"
    )
    confidence_score = models.FloatField(
        null=True, 
        blank=True, 
        help_text="Score de confiança da IA (0.0 a 1.0)"
    )
    modelo_ia = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Modelo de IA usado (ex: gpt-4o, claude-3.5-sonnet)"
    )
    prompt_version = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        help_text="Versão do prompt template usado"
    )
    
    # Edições do médico
    doctor_edit = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Detalhes da edição: {medicamento_index, campo_editado, valor_original, valor_editado, motivo}"
    )
    manual_override_reason = models.TextField(
        null=True, 
        blank=True, 
        help_text="Motivo do override manual (ex: contraindicação ignorada)"
    )
    break_glass_confirmed = models.BooleanField(
        null=True, 
        blank=True, 
        help_text="Confirmação de break glass (ex: medicamento categoria D/X em gravidez)"
    )
    
    # Prescrição final
    final_prescription = models.JSONField(
        null=True, 
        blank=True, 
        help_text="Prescrição final validada pelo médico"
    )
    
    # PDF gerado
    pdf_hash = models.CharField(
        max_length=64, 
        null=True, 
        blank=True, 
        help_text="Hash SHA-256 do PDF gerado para integridade"
    )
    pdf_generated_at = models.DateTimeField(
        null=True, 
        blank=True, 
        help_text="Data/hora de geração do PDF"
    )
    
    # Metadados de rastreabilidade
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="IP da requisição")
    user_agent = models.TextField(null=True, blank=True, help_text="User agent do navegador")
    session_id = models.CharField(
        max_length=255, 
        null=True, 
        blank=True, 
        help_text="ID da sessão para rastreamento"
    )
    
    # Campos de compliance
    lgpd_compliant = models.BooleanField(
        default=True, 
        help_text="Confirma que nenhum PII foi armazenado neste registro"
    )
    anvisa_compliant = models.BooleanField(
        default=True, 
        help_text="Confirma conformidade com RDC 657/2022"
    )

    objects = HospitalScopedManager()

    def __str__(self):
        consulta_ref = f"Consulta {self.consulta_id}" if self.consulta_id else "N/A"
        return f"{self.get_action_display()} - {consulta_ref} - {self.timestamp}"

    class Meta:
        verbose_name = "Audit Trail"
        verbose_name_plural = "Audit Trails"
        indexes = [
            models.Index(fields=["hospital", "timestamp"]),
            models.Index(fields=["hospital", "action", "timestamp"]),
            models.Index(fields=["consulta", "timestamp"]),
            models.Index(fields=["receita", "timestamp"]),
            models.Index(fields=["user", "timestamp"]),
        ]
        ordering = ["-timestamp"]


class PromptTemplate(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    versao = models.PositiveIntegerField()
    conteudo = models.TextField()
    ativo = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]


class HospitalKnowledgeItem(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=100)
    texto = models.TextField()
    aprovado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    versao = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]


class AiDraft(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    consulta = models.ForeignKey(Consulta, on_delete=models.CASCADE, null=True, blank=True)
    input_sem_pii = models.JSONField()
    output_json = models.JSONField()
    modelo = models.CharField(max_length=50)
    prompt_version = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]


class AiFeedback(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    draft = models.ForeignKey(AiDraft, on_delete=models.CASCADE)
    medico = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField()
    motivo = models.TextField(blank=True)
    correcoes_json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]


class BulaCache(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=255)
    url = models.URLField()
    url_pdf = models.URLField(blank=True, null=True)
    conteudo = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]


class BulaAccessLog(models.Model):
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    url = models.URLField()
    titulo = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    class Meta:
        indexes = [models.Index(fields=["hospital"])]
