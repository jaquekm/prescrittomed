from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Consulta, Hospital, Paciente


class Command(BaseCommand):
    help = "Executa um smoke test de isolamento multi-tenant entre dois hospitais."

    def handle(self, *args, **options):
        User = get_user_model()

        unique_suffix = uuid4().hex[:8]
        try:
            with transaction.atomic():
                hospital_a = Hospital.objects.create(
                    nome="Hospital A",
                    cnpj=f"TENANT-A-{unique_suffix}",
                    endereco="Rua A",
                )
                hospital_b = Hospital.objects.create(
                    nome="Hospital B",
                    cnpj=f"TENANT-B-{unique_suffix}",
                    endereco="Rua B",
                )
                medico_a = User.objects.create_user(
                    username=f"tenant_medico_a_{unique_suffix}",
                    password="senha",
                    tipo="MEDICO",
                    hospital=hospital_a,
                )
                medico_b = User.objects.create_user(
                    username=f"tenant_medico_b_{unique_suffix}",
                    password="senha",
                    tipo="MEDICO",
                    hospital=hospital_b,
                )
                paciente_b = Paciente.objects.create(
                    hospital=hospital_b,
                    nome_completo="Paciente B",
                    data_nascimento="1990-01-01",
                    cpf=f"tenant-{unique_suffix}",
                )
                consulta_b = Consulta.objects.create(
                    paciente=paciente_b,
                    medico=medico_b,
                    hospital=hospital_b,
                    sintomas="Teste",
                    analise_ia="Teste",
                    prescricao="Teste",
                )

                if Paciente.objects.for_user(medico_a).filter(id=paciente_b.id).exists():
                    raise CommandError("Falha: médico do Hospital A acessou paciente do Hospital B.")

                if Consulta.objects.for_user(medico_a).filter(id=consulta_b.id).exists():
                    raise CommandError("Falha: médico do Hospital A acessou consulta do Hospital B.")

                self.stdout.write(self.style.SUCCESS("Smoke test multi-tenant OK."))
        finally:
            Consulta.objects.filter(hospital__cnpj__icontains=unique_suffix).delete()
            Paciente.objects.filter(hospital__cnpj__icontains=unique_suffix).delete()
            User.objects.filter(username__icontains=unique_suffix).delete()
            Hospital.objects.filter(cnpj__icontains=unique_suffix).delete()
