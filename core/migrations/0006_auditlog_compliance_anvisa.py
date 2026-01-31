# Generated manually for SmartRx AI - ANVISA RDC 657/2022 Compliance
# Expande AuditLog para rastreabilidade completa: Input, AI Suggestion, Doctor Edit, Final PDF

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_perfilmedico_alter_usuario_options_and_more'),
    ]

    operations = [
        # Remover campos antigos que não são mais necessários
        migrations.RemoveField(
            model_name='auditlog',
            name='object_type',
        ),
        migrations.RemoveField(
            model_name='auditlog',
            name='object_id',
        ),
        
        # Alterar campo action para usar choices
        migrations.AlterField(
            model_name='auditlog',
            name='action',
            field=models.CharField(
                choices=[
                    ('INPUT_RECEIVED', 'Input Recebido'),
                    ('AI_SUGGESTION_GENERATED', 'Sugestão IA Gerada'),
                    ('DOCTOR_EDIT', 'Edição do Médico'),
                    ('MANUAL_OVERRIDE', 'Override Manual'),
                    ('PRESCRIPTION_FINALIZED', 'Prescrição Finalizada'),
                    ('PDF_GENERATED', 'PDF Gerado'),
                    ('BREAK_GLASS_CONFIRMATION', 'Confirmação Break Glass'),
                ],
                max_length=50
            ),
        ),
        
        # Adicionar relacionamentos com Consulta e Receita
        migrations.AddField(
            model_name='auditlog',
            name='consulta',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='audit_logs',
                to='core.consulta'
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='receita',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='audit_logs',
                to='core.receita'
            ),
        ),
        
        # Dados de entrada (sanitizados)
        migrations.AddField(
            model_name='auditlog',
            name='input_data',
            field=models.JSONField(blank=True, help_text='Dados de entrada sanitizados', null=True),
        ),
        
        # Sugestão da IA
        migrations.AddField(
            model_name='auditlog',
            name='ai_suggestion',
            field=models.JSONField(blank=True, help_text='Sugestão completa da IA em JSON', null=True),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='source_ids_used',
            field=models.JSONField(
                blank=True,
                help_text='Lista de source_ids das fontes consultadas pela IA',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='confidence_score',
            field=models.FloatField(
                blank=True,
                help_text='Score de confiança da IA (0.0 a 1.0)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='modelo_ia',
            field=models.CharField(
                blank=True,
                help_text='Modelo de IA usado (ex: gpt-4o, claude-3.5-sonnet)',
                max_length=50,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='prompt_version',
            field=models.PositiveIntegerField(
                blank=True,
                help_text='Versão do prompt template usado',
                null=True
            ),
        ),
        
        # Edições do médico
        migrations.AddField(
            model_name='auditlog',
            name='doctor_edit',
            field=models.JSONField(
                blank=True,
                help_text='Detalhes da edição: {medicamento_index, campo_editado, valor_original, valor_editado, motivo}',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='manual_override_reason',
            field=models.TextField(
                blank=True,
                help_text='Motivo do override manual (ex: contraindicação ignorada)',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='break_glass_confirmed',
            field=models.BooleanField(
                blank=True,
                help_text='Confirmação de break glass (ex: medicamento categoria D/X em gravidez)',
                null=True
            ),
        ),
        
        # Prescrição final
        migrations.AddField(
            model_name='auditlog',
            name='final_prescription',
            field=models.JSONField(
                blank=True,
                help_text='Prescrição final validada pelo médico',
                null=True
            ),
        ),
        
        # PDF gerado
        migrations.AddField(
            model_name='auditlog',
            name='pdf_hash',
            field=models.CharField(
                blank=True,
                help_text='Hash SHA-256 do PDF gerado para integridade',
                max_length=64,
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='pdf_generated_at',
            field=models.DateTimeField(
                blank=True,
                help_text='Data/hora de geração do PDF',
                null=True
            ),
        ),
        
        # Metadados de rastreabilidade
        migrations.AddField(
            model_name='auditlog',
            name='ip_address',
            field=models.GenericIPAddressField(
                blank=True,
                help_text='IP da requisição',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='user_agent',
            field=models.TextField(
                blank=True,
                help_text='User agent do navegador',
                null=True
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='session_id',
            field=models.CharField(
                blank=True,
                help_text='ID da sessão para rastreamento',
                max_length=255,
                null=True
            ),
        ),
        
        # Campos de compliance
        migrations.AddField(
            model_name='auditlog',
            name='lgpd_compliant',
            field=models.BooleanField(
                default=True,
                help_text='Confirma que nenhum PII foi armazenado neste registro'
            ),
        ),
        migrations.AddField(
            model_name='auditlog',
            name='anvisa_compliant',
            field=models.BooleanField(
                default=True,
                help_text='Confirma conformidade com RDC 657/2022'
            ),
        ),
        
        # Adicionar índice ao timestamp para melhor performance
        migrations.AlterField(
            model_name='auditlog',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, db_index=True),
        ),
        
        # Adicionar novos índices para queries otimizadas
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['hospital', 'timestamp'], name='core_auditl_hospita_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['hospital', 'action', 'timestamp'], name='core_auditl_hospita_action_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['consulta', 'timestamp'], name='core_auditl_consulta_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['receita', 'timestamp'], name='core_auditl_receita_timesta_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user', 'timestamp'], name='core_auditl_user_timesta_idx'),
        ),
    ]
