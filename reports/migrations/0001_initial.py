# Generated by Django 5.2.2 on 2025-06-18 12:36

import django.core.validators
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Dashboard',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('layout', models.JSONField(default=dict, verbose_name='layout')),
                ('is_public', models.BooleanField(default=False, verbose_name='is public')),
                ('refresh_interval', models.PositiveIntegerField(default=0, verbose_name='refresh interval')),
                ('last_refresh', models.DateTimeField(blank=True, null=True, verbose_name='last refresh')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
            ],
            options={
                'verbose_name': 'dashboard',
                'verbose_name_plural': 'dashboards',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='DashboardWidget',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('widget_type', models.CharField(choices=[('CHART', 'Chart'), ('TABLE', 'Table'), ('METRIC', 'Metric'), ('LIST', 'List'), ('CUSTOM', 'Custom')], max_length=20, verbose_name='widget type')),
                ('data_source', models.CharField(max_length=200, verbose_name='data source')),
                ('configuration', models.JSONField(default=dict, verbose_name='configuration')),
                ('position', models.JSONField(default=dict, verbose_name='position')),
                ('size', models.JSONField(default=dict, verbose_name='size')),
                ('refresh_interval', models.PositiveIntegerField(default=0, verbose_name='refresh interval')),
                ('last_refresh', models.DateTimeField(blank=True, null=True, verbose_name='last refresh')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
            ],
            options={
                'verbose_name': 'dashboard widget',
                'verbose_name_plural': 'dashboard widgets',
                'ordering': ['position'],
            },
        ),
        migrations.CreateModel(
            name='Report',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='is active')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('report_type', models.CharField(choices=[('COMPLAINT', 'Complaint Report'), ('PERFORMANCE', 'Performance Report'), ('SATISFACTION', 'Satisfaction Report'), ('DEPARTMENT', 'Department Report'), ('CUSTOM', 'Custom Report')], max_length=20, verbose_name='report type')),
                ('format', models.CharField(choices=[('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV'), ('JSON', 'JSON')], default='PDF', max_length=10, verbose_name='format')),
                ('is_template', models.BooleanField(default=False, verbose_name='is template')),
                ('parameters', models.JSONField(default=dict, verbose_name='parameters')),
                ('last_generated', models.DateTimeField(blank=True, null=True, verbose_name='last generated')),
                ('file', models.FileField(blank=True, null=True, upload_to='reports/%Y/%m/', verbose_name='file')),
                ('is_public', models.BooleanField(default=False, verbose_name='is public')),
                ('access_level', models.PositiveSmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(5)], verbose_name='access level')),
            ],
            options={
                'verbose_name': 'report',
                'verbose_name_plural': 'reports',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportLog',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_active', models.BooleanField(db_index=True, default=True, verbose_name='is active')),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('status', models.CharField(choices=[('PENDING', 'Pending'), ('RUNNING', 'Running'), ('COMPLETED', 'Completed'), ('FAILED', 'Failed'), ('CANCELLED', 'Cancelled')], max_length=20, verbose_name='status')),
                ('started_at', models.DateTimeField(verbose_name='started at')),
                ('completed_at', models.DateTimeField(blank=True, null=True, verbose_name='completed at')),
                ('duration', models.DurationField(blank=True, null=True, verbose_name='duration')),
                ('error_message', models.TextField(blank=True, verbose_name='error message')),
                ('parameters', models.JSONField(default=dict, verbose_name='parameters')),
                ('file_size', models.PositiveIntegerField(blank=True, null=True, verbose_name='file size')),
                ('file_path', models.CharField(blank=True, max_length=500, verbose_name='file path')),
            ],
            options={
                'verbose_name': 'report log',
                'verbose_name_plural': 'report logs',
                'ordering': ['-started_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportSchedule',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('frequency', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('QUARTERLY', 'Quarterly'), ('YEARLY', 'Yearly'), ('CUSTOM', 'Custom')], max_length=20, verbose_name='frequency')),
                ('cron_expression', models.CharField(blank=True, max_length=100, verbose_name='cron expression')),
                ('start_date', models.DateTimeField(verbose_name='start date')),
                ('end_date', models.DateTimeField(blank=True, null=True, verbose_name='end date')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('last_run', models.DateTimeField(blank=True, null=True, verbose_name='last run')),
                ('next_run', models.DateTimeField(blank=True, null=True, verbose_name='next run')),
                ('parameters', models.JSONField(default=dict, verbose_name='parameters')),
            ],
            options={
                'verbose_name': 'report schedule',
                'verbose_name_plural': 'report schedules',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ReportTemplate',
            fields=[
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True, verbose_name='updated at')),
                ('id', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('deleted_at', models.DateTimeField(blank=True, null=True, verbose_name='deleted at')),
                ('name', models.CharField(max_length=200, verbose_name='name')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('template_file', models.FileField(upload_to='reports/templates/', verbose_name='template file')),
                ('report_type', models.CharField(choices=[('COMPLAINT', 'Complaint Report'), ('PERFORMANCE', 'Performance Report'), ('SATISFACTION', 'Satisfaction Report'), ('DEPARTMENT', 'Department Report'), ('CUSTOM', 'Custom Report')], max_length=20, verbose_name='report type')),
                ('format', models.CharField(choices=[('PDF', 'PDF'), ('EXCEL', 'Excel'), ('CSV', 'CSV'), ('JSON', 'JSON')], max_length=10, verbose_name='format')),
                ('parameters', models.JSONField(default=dict, verbose_name='parameters')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('version', models.PositiveIntegerField(default=1, verbose_name='version')),
            ],
            options={
                'verbose_name': 'report template',
                'verbose_name_plural': 'report templates',
                'ordering': ['-created_at'],
            },
        ),
    ]
