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
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    hospital = models.ForeignKey(Hospital, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = HospitalScopedManager()

    def __str__(self):
        return f"{self.action} - {self.object_type}:{self.object_id}"

    class Meta:
        indexes = [
            models.Index(fields=["hospital"]),
        ]


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
