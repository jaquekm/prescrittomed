from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_perfilmedico_alter_usuario_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="pode_ver_todos_pacientes",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="paciente",
            name="medico_responsavel",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="pacientes_responsaveis",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="consulta",
            name="status",
            field=models.CharField(
                choices=[
                    ("EM_ANDAMENTO", "Em andamento"),
                    ("RASCUNHO_SALVO", "Rascunho salvo"),
                    ("EM_REVISAO", "Em revisão"),
                    ("ASSINADA", "Assinada"),
                    ("ARQUIVADA", "Arquivada"),
                ],
                default="EM_ANDAMENTO",
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name="consulta",
            name="chat_messages",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.CreateModel(
            name="HospitalConfig",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("dominios_permitidos", models.TextField(blank=True)),
                ("modo_privacidade", models.BooleanField(default=False)),
                ("retencao_dados_dias", models.PositiveIntegerField(default=365)),
                ("assinatura_rodape", models.TextField(blank=True)),
                ("estilo_orientacao", models.TextField(blank=True)),
                ("defaults_orientacao", models.TextField(blank=True)),
                ("hospital", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to="core.hospital")),
            ],
        ),
        migrations.CreateModel(
            name="MedicoInvite",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("PENDENTE", "Pendente"), ("ACEITO", "Aceito"), ("EXPIRADO", "Expirado")], default="PENDENTE", max_length=20)),
                ("token", models.CharField(max_length=255)),
                ("expires_at", models.DateTimeField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("hospital", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="core.hospital")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddIndex(
            model_name="hospitalconfig",
            index=models.Index(fields=["hospital"], name="core_hospi_hospital_idx"),
        ),
        migrations.AddIndex(
            model_name="medicoinvite",
            index=models.Index(fields=["hospital"], name="core_medico_hospital_idx"),
        ),
    ]
