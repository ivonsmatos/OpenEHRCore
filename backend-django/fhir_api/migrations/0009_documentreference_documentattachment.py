# Generated migration for DocumentReference and DocumentAttachment models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.contrib.postgres.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fhir_api', '0008_previous_migration'),  # Ajustar para a migração anterior real
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentReference',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('current', 'Atual'), ('superseded', 'Substituído'), ('entered-in-error', 'Erro de Entrada')], default='current', max_length=20)),
                ('doc_status', models.CharField(choices=[('preliminary', 'Preliminar'), ('final', 'Final'), ('amended', 'Emendado'), ('entered-in-error', 'Erro de Entrada')], default='final', max_length=20)),
                ('type', models.CharField(choices=[('lab-report', 'Resultado Laboratorial'), ('imaging-report', 'Laudo de Imagem'), ('prescription', 'Prescrição'), ('discharge-summary', 'Sumário de Alta'), ('progress-note', 'Nota de Evolução'), ('consent-form', 'Termo de Consentimento'), ('referral', 'Encaminhamento'), ('other', 'Outro')], max_length=50)),
                ('category', models.CharField(blank=True, max_length=50, null=True)),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('security_label', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(choices=[('N', 'Normal'), ('R', 'Restricted'), ('V', 'Very Restricted')], max_length=1), blank=True, default=list, size=None)),
                ('content', models.JSONField(default=list, help_text='FHIR DocumentReference.content array')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('authenticator', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authenticated_documents', to=settings.AUTH_USER_MODEL)),
                ('author', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='authored_documents', to=settings.AUTH_USER_MODEL)),
                ('encounter', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='fhir_api.encounter')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to='fhir_api.patient')),
                ('supersedes', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='superseded_by', to='fhir_api.documentreference')),
            ],
            options={
                'verbose_name': 'Document Reference',
                'verbose_name_plural': 'Document References',
                'ordering': ['-date'],
                'indexes': [
                    models.Index(fields=['patient', '-date'], name='fhir_api_do_patient_date_idx'),
                    models.Index(fields=['type', '-date'], name='fhir_api_do_type_date_idx'),
                    models.Index(fields=['status'], name='fhir_api_do_status_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='DocumentAttachment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('file', models.FileField(upload_to='documents/%Y/%m/%d/')),
                ('content_type', models.CharField(max_length=100)),
                ('size', models.IntegerField(help_text='Size in bytes')),
                ('title', models.CharField(max_length=255)),
                ('hash_sha256', models.CharField(blank=True, max_length=64)),
                ('url', models.URLField(blank=True, max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('document', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attachments', to='fhir_api.documentreference')),
            ],
            options={
                'verbose_name': 'Document Attachment',
                'verbose_name_plural': 'Document Attachments',
                'ordering': ['created_at'],
            },
        ),
    ]
