from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils import timezone

from core.models import AuditLog, Consulta, Hospital, MedicoInvite, Paciente, Receita


class InviteAndScopeTests(TestCase):
    def setUp(self):
        self.hospital_a = Hospital.objects.create(nome="Hospital A", cnpj="1", endereco="Rua A")
        self.hospital_b = Hospital.objects.create(nome="Hospital B", cnpj="2", endereco="Rua B")
        self.admin_a = get_user_model().objects.create_user(
            username="admina",
            email="admina@example.com",
            password="senha123",
            tipo="ADMIN",
            hospital=self.hospital_a,
        )

    def test_invite_flow_activates_user_and_logs(self):
        medico = get_user_model().objects.create_user(
            username="medico",
            email="medico@example.com",
            password=None,
            tipo="MEDICO",
            hospital=self.hospital_a,
            is_active=False,
        )
        token = PasswordResetTokenGenerator().make_token(medico)
        MedicoInvite.objects.create(
            user=medico,
            hospital=self.hospital_a,
            token=token,
            expires_at=timezone.now() + timezone.timedelta(days=7),
        )
        uid = urlsafe_base64_encode(force_bytes(medico.pk))
        response = self.client.post(
            reverse("aceitar_convite", kwargs={"uidb64": uid, "token": token}),
            {"new_password1": "Senha#123", "new_password2": "Senha#123"},
        )
        medico.refresh_from_db()
        self.assertTrue(medico.is_active)
        self.assertTrue(AuditLog.objects.filter(action="aceitar_convite", object_id=str(medico.id)).exists())
        self.assertEqual(response.status_code, 302)

    def test_hospital_scope_blocks_other_hospital_patient(self):
        paciente_b = Paciente.objects.create(
            hospital=self.hospital_b,
            nome_completo="Paciente B",
            data_nascimento="1990-01-01",
            cpf="123.456.789-00",
        )
        self.client.force_login(self.admin_a)
        response = self.client.get(reverse("paciente_detalhe", args=[paciente_b.id]))
        self.assertEqual(response.status_code, 403)

    def test_assinar_requires_revisao_status(self):
        medico = get_user_model().objects.create_user(
            username="medicob",
            email="medicob@example.com",
            password="senha123",
            tipo="MEDICO",
            hospital=self.hospital_a,
        )
        paciente = Paciente.objects.create(
            hospital=self.hospital_a,
            nome_completo="Paciente A",
            data_nascimento="1990-01-01",
            cpf="987.654.321-00",
        )
        consulta = Consulta.objects.create(
            paciente=paciente,
            medico=medico,
            hospital=self.hospital_a,
            sintomas="Teste",
            status=Consulta.STATUS_RASCUNHO_SALVO,
        )
        Receita.objects.create(
            consulta=consulta,
            hospital=self.hospital_a,
            version=1,
            status=Receita.STATUS_RASCUNHO,
            json_content={
                "resumo_tecnico_medico": [],
                "orientacoes_ao_paciente": [],
                "medicamentos": [],
                "alertas_seguranca": [],
                "monitorizacao": [],
                "fontes": [],
            },
            created_by=medico,
        )
        self.client.force_login(medico)
        response = self.client.post(
            reverse("revisar_receita", args=[consulta.id]),
            {"acao": "assinar_revisao"},
        )
        consulta.refresh_from_db()
        self.assertNotEqual(consulta.status, Consulta.STATUS_ASSINADA)
        self.assertEqual(response.status_code, 302)

    def test_assinar_creates_audit_log(self):
        medico = get_user_model().objects.create_user(
            username="medicoc",
            email="medicoc@example.com",
            password="senha123",
            tipo="MEDICO",
            hospital=self.hospital_a,
        )
        paciente = Paciente.objects.create(
            hospital=self.hospital_a,
            nome_completo="Paciente C",
            data_nascimento="1990-01-01",
            cpf="111.222.333-44",
        )
        consulta = Consulta.objects.create(
            paciente=paciente,
            medico=medico,
            hospital=self.hospital_a,
            sintomas="Teste",
            status=Consulta.STATUS_EM_REVISAO,
        )
        receita = Receita.objects.create(
            consulta=consulta,
            hospital=self.hospital_a,
            version=1,
            status=Receita.STATUS_RASCUNHO,
            json_content={
                "resumo_tecnico_medico": [],
                "orientacoes_ao_paciente": [],
                "medicamentos": [],
                "alertas_seguranca": [],
                "monitorizacao": [],
                "fontes": [],
            },
            created_by=medico,
        )
        self.client.force_login(medico)
        response = self.client.post(
            reverse("revisar_receita", args=[consulta.id]),
            {"acao": "assinar_revisao"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(AuditLog.objects.filter(action="ASSINATURA_ACEITE_IA", object_id=str(receita.id)).exists())
