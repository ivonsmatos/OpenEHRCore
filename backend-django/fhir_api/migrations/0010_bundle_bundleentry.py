# Generated migration for Bundle and BundleEntry models

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('fhir_api', '0009_documentreference_documentattachment'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bundle',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('identifier', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('type', models.CharField(choices=[('document', 'Document'), ('message', 'Message'), ('transaction', 'Transaction'), ('transaction-response', 'Transaction Response'), ('batch', 'Batch'), ('batch-response', 'Batch Response'), ('history', 'History List'), ('searchset', 'Search Results'), ('collection', 'Collection')], max_length=30)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('total', models.IntegerField(blank=True, help_text='Total de recursos encontrados', null=True)),
                ('entries', models.JSONField(default=list, help_text='Array de BundleEntry (fullUrl, resource, request, response)')),
                ('status', models.CharField(choices=[('pending', 'Pendente'), ('processing', 'Processando'), ('completed', 'Completo'), ('failed', 'Falhou')], default='pending', max_length=20)),
                ('result_message', models.TextField(blank=True, null=True)),
                ('failed_entries', models.JSONField(default=list, help_text='Entradas que falharam')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_bundles', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'FHIR Bundle',
                'verbose_name_plural': 'FHIR Bundles',
                'ordering': ['-timestamp'],
                'indexes': [
                    models.Index(fields=['-timestamp'], name='fhir_api_bu_timesta_idx'),
                    models.Index(fields=['type', '-timestamp'], name='fhir_api_bu_type_time_idx'),
                    models.Index(fields=['status'], name='fhir_api_bu_status_idx'),
                    models.Index(fields=['created_by', '-timestamp'], name='fhir_api_bu_created_time_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='BundleEntry',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('full_url', models.URLField(blank=True, max_length=500, null=True)),
                ('resource_type', models.CharField(max_length=50)),
                ('resource_id', models.CharField(blank=True, max_length=255, null=True)),
                ('request_method', models.CharField(blank=True, choices=[('GET', 'GET'), ('POST', 'POST'), ('PUT', 'PUT'), ('PATCH', 'PATCH'), ('DELETE', 'DELETE')], max_length=10, null=True)),
                ('request_url', models.CharField(blank=True, max_length=500, null=True)),
                ('response_status', models.CharField(blank=True, max_length=10, null=True)),
                ('response_location', models.URLField(blank=True, max_length=500, null=True)),
                ('response_etag', models.CharField(blank=True, max_length=100, null=True)),
                ('response_last_modified', models.DateTimeField(blank=True, null=True)),
                ('resource_json', models.JSONField()),
                ('processed', models.BooleanField(default=False)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bundle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='entry_records', to='fhir_api.bundle')),
            ],
            options={
                'verbose_name': 'Bundle Entry',
                'verbose_name_plural': 'Bundle Entries',
                'ordering': ['created_at'],
                'indexes': [
                    models.Index(fields=['bundle', 'resource_type'], name='fhir_api_be_bundle_res_idx'),
                    models.Index(fields=['resource_type', 'resource_id'], name='fhir_api_be_restype_id_idx'),
                ],
            },
        ),
    ]
