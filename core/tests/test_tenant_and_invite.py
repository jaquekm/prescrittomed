from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from core.models import AuditLog, Consulta, Hospital, Paciente, Receita
from core.services.openai_prescription import generate_prescription


class TenantIsolationTests(TestCase):
    def setUp(self):
        self.hospital_a = Hospital.objects.create(nome="Hospital A", cnpj="0001", endereco="Rua A")
        self.hospital_b = Hospital.objects.create(nome="Hospital B", cnpj="0002", endereco="Rua B")
        User = get_user_model()
        self.medico_a = User.objects.create_user(
            username="medico_a",
            password="senha",
            tipo="MEDICO",
            hospital=self.hospital_a,
        )
        self.medico_b = User.objects.create_user(
            username="medico_b",
            password="senha",
            tipo="MEDICO",
            hospital=self.hospital_b,
        )
        self.paciente_b = Paciente.objects.create(
            hospital=self.hospital_b,
            nome_completo="Paciente B",
            data_nascimento="1990-01-01",
            cpf="00000000000",
        )
        self.consulta_b = Consulta.objects.create(
            paciente=self.paciente_b,
            medico=self.medico_b,
            hospital=self.hospital_b,
            sintomas="Teste",
            analise_ia="Teste",
            prescricao="Teste",
        )

    def test_medico_nao_acessa_consulta_outro_hospital(self):
        self.client.force_login(self.medico_a)
        url = reverse("gerar_receita", kwargs={"consulta_id": self.consulta_b.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)


class InviteFlowTests(TestCase):
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_convite_medico_ativa_usuario(self):
        hospital = Hospital.objects.create(nome="Hospital C", cnpj="0003", endereco="Rua C")
        User = get_user_model()
        admin = User.objects.create_user(
            username="admin",
            password="senha",
            tipo="ADMIN",
            is_staff=True,
        )
        self.client.force_login(admin)
        response = self.client.post(
            reverse("convidar_medico"),
            {
                "nome_usuario": "medico_convite",
                "email": "medico@example.com",
                "crm": "12345",
                "hospital": hospital.id,
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        email_body = mail.outbox[0].body
        link = next(line for line in email_body.splitlines() if line.startswith("http"))
        response = self.client.get(link)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(
            link,
            {"new_password1": "NovaSenha123!", "new_password2": "NovaSenha123!"},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        medico = User.objects.get(username="medico_convite")
        self.assertTrue(medico.is_active)


class AuditLogAcceptanceTests(TestCase):
    def test_modal_assinatura_registra_auditlog(self):
        hospital = Hospital.objects.create(nome="Hospital D", cnpj="0004", endereco="Rua D")
        User = get_user_model()
        medico = User.objects.create_user(
            username="medico_assina",
            password="senha",
            tipo="MEDICO",
            hospital=hospital,
        )
        paciente = Paciente.objects.create(
            hospital=hospital,
            nome_completo="Paciente D",
            data_nascimento="1990-01-01",
            cpf="00000000001",
        )
        consulta = Consulta.objects.create(
            paciente=paciente,
            medico=medico,
            hospital=hospital,
            sintomas="Teste",
            analise_ia="Teste",
            prescricao="Teste",
        )
        Receita.objects.create(
            consulta=consulta,
            hospital=hospital,
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
            reverse("atendimento"),
            {"acao": "finalizar_receita", "consulta_id": consulta.id},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(AuditLog.objects.filter(action="ASSINATURA_ACEITE_IA").exists())

        response = self.client.post(
            reverse("atendimento"),
            {
                "acao": "finalizar_receita",
                "consulta_id": consulta.id,
                "confirmacao_1": "on",
                "confirmacao_2": "on",
                "confirmacao_3": "on",
                "confirmacao_4": "on",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(AuditLog.objects.filter(action="ASSINATURA_ACEITE_IA").exists())


class OpenAIPrescriptionTests(TestCase):
    def test_generate_prescription_removes_pii(self):
        fake_response = SimpleNamespace(
            output_text='{"resumo_tecnico_medico":[],"orientacoes_ao_paciente":[],"medicamentos":[{"nome":"X","principio_ativo":"X","forma":"comprimido","concentracao":"10mg","posologia":"1x/dia","via":"oral","frequencia":"diária","duracao":"5 dias"}],"alertas_seguranca":[],"monitorizacao":[],"fontes":[]}'
        )
        captured = {}

        class FakeResponses:
            def create(self, **kwargs):
                captured["payload"] = kwargs["input"][1]["content"]
                return fake_response

        class FakeClient:
            def __init__(self, api_key):
                self.responses = FakeResponses()

        with patch("core.services.openai_prescription.OpenAI", FakeClient):
            contexto = {"nome": "Paciente", "cpf": "123", "sintomas": "Dor CPF 123.456.789-00"}
            result = generate_prescription(contexto)
            self.assertIn("medicamentos", result)
            self.assertNotIn("nome", captured["payload"])
            self.assertNotIn("cpf", captured["payload"])
            self.assertNotIn("123.456.789-00", captured["payload"])
