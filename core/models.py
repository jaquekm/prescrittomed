from django.db import models
from django.contrib.auth.models import User

# 1. O HOSPITAL (Quem paga a conta)
class Hospital(models.Model):
    nome = models.CharField(max_length=100)
    cnpj = models.CharField(max_length=20)
    endereco = models.TextField()
    # Novos campos de customização
    logo = models.ImageField(upload_to='logos_hospitais/', null=True, blank=True)
    cor_primaria = models.CharField(max_length=7, default='#2c3e50', help_text="Código Hex da cor (ex: #000000)")
    data_criacao = models.DateTimeField(auto_now_add=True)
    
    # O Administrador da conta desse hospital
    admin_responsavel = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="hospitais_geridos")

    def __str__(self):
        return self.nome

# 2. O PERFIL DO MÉDICO (Extensão do Usuário)
class PerfilMedico(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_medico')
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
    cpf = models.CharField(max_length=14, unique=True)
    historico_alergias = models.TextField(blank=True)
    
    def __str__(self):
        return self.nome_completo

# 4. A CONSULTA (Ligada ao histórico)
class Consulta(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    medico = models.ForeignKey(User, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    sintomas = models.TextField() # Histórico do Chat
    analise_ia = models.TextField(null=True, blank=True) # Parte técnica
    prescricao = models.TextField(null=True, blank=True) # Receita final editada
    
    def __str__(self):
        return f"{self.paciente.nome_completo} - {self.data}"