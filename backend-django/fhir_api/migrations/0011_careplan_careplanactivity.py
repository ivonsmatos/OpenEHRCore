# Generated migration for CarePlan and CarePlanActivity models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fhir_api', '0010_bundle_bundleentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarePlan',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('identifier', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('status', models.CharField(choices=[('draft', 'Rascunho'), ('active', 'Ativo'), ('on-hold', 'Em Espera'), ('revoked', 'Revogado'), ('completed', 'Completo'), ('entered-in-error', 'Erro de Entrada'), ('unknown', 'Desconhecido')], default='draft', max_length=20)),
                ('intent', models.CharField(choices=[('proposal', 'Proposta'), ('plan', 'Plano'), ('order', 'Ordem'), ('option', 'Opção')], default='plan', max_length=20)),
                ('categories', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('assess-plan', 'Assessment and Plan'), ('careteam', 'Care Team Coordination'), ('episodeofcare', 'Episode of Care'), ('longitudinal', 'Longitudinal Care'), ('multidisciplinary', 'Multidisciplinary Care'), ('perioperative', 'Perioperative Care'), ('rehabilitation', 'Rehabilitation'), ('other', 'Other')], max_length=50), blank=True, default=list, size=None)),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('period_start', models.DateTimeField()),
                ('period_end', models.DateTimeField(blank=True, null=True)),
                ('addresses', models.JSONField(default=list, help_text='Condições/problemas que o plano endereça')),
                ('goals', models.JSONField(default=list, help_text='Array de referências para Goal resources')),
                ('notes', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authored_careplans', to=settings.AUTH_USER_MODEL)),
                ('care_team', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='care_plans', to='fhir_api.careteam')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_careplans', to=settings.AUTH_USER_MODEL)),
                ('encounter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='care_plans', to='fhir_api.encounter')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='care_plans', to='fhir_api.patient')),
            ],
            options={
                'verbose_name': 'Care Plan',
                'verbose_name_plural': 'Care Plans',
                'ordering': ['-period_start'],
                'indexes': [
                    models.Index(fields=['patient', '-period_start'], name='fhir_api_cp_patient_period_idx'),
                    models.Index(fields=['status', '-period_start'], name='fhir_api_cp_status_period_idx'),
                    models.Index(fields=['author', '-created_at'], name='fhir_api_cp_author_created_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='CarePlanActivity',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('not-started', 'Não Iniciado'), ('scheduled', 'Agendado'), ('in-progress', 'Em Progresso'), ('on-hold', 'Em Espera'), ('completed', 'Completo'), ('cancelled', 'Cancelado'), ('stopped', 'Parado'), ('unknown', 'Desconhecido'), ('entered-in-error', 'Erro de Entrada')], default='not-started', max_length=20)),
                ('outcome_codeable_concept', models.JSONField(blank=True, null=True)),
                ('outcome_reference', models.JSONField(blank=True, null=True)),
                ('progress', models.TextField(blank=True, null=True)),
                ('kind', models.CharField(blank=True, choices=[('Appointment', 'Consulta'), ('CommunicationRequest', 'Solicitação de Comunicação'), ('DeviceRequest', 'Solicitação de Dispositivo'), ('MedicationRequest', 'Prescrição'), ('NutritionOrder', 'Ordem de Nutrição'), ('Task', 'Tarefa'), ('ServiceRequest', 'Solicitação de Serviço'), ('VisionPrescription', 'Prescrição de Visão')], max_length=50, null=True)),
                ('code', models.JSONField(help_text='Código da atividade (SNOMED CT)')),
                ('reason_code', models.JSONField(blank=True, null=True)),
                ('reason_reference', models.JSONField(blank=True, null=True)),
                ('goal', models.JSONField(default=list, help_text='Referências para Goal resources')),
                ('description', models.TextField(blank=True, null=True)),
                ('scheduled_timing', models.JSONField(blank=True, help_text='Timing para atividades recorrentes', null=True)),
                ('scheduled_period_start', models.DateTimeField(blank=True, null=True)),
                ('scheduled_period_end', models.DateTimeField(blank=True, null=True)),
                ('scheduled_string', models.CharField(blank=True, max_length=255, null=True)),
                ('performers', models.JSONField(default=list, help_text='Profissionais responsáveis pela atividade')),
                ('product_reference', models.JSONField(blank=True, null=True)),
                ('daily_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('quantity', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('care_plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='activities', to='fhir_api.careplan')),
                ('location', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='careplan_activities', to='fhir_api.location')),
            ],
            options={
                'verbose_name': 'CarePlan Activity',
                'verbose_name_plural': 'CarePlan Activities',
                'ordering': ['scheduled_period_start', 'created_at'],
                'indexes': [
                    models.Index(fields=['care_plan', 'status'], name='fhir_api_cpa_careplan_status_idx'),
                    models.Index(fields=['status', 'scheduled_period_start'], name='fhir_api_cpa_status_sched_idx'),
                ],
            },
        ),
    ]
