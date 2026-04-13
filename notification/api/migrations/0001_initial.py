from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('subject', models.CharField(max_length=255)),
                ('body', models.TextField(help_text='Use {{variable}} placeholders. Can be HTML.')),
                ('is_html', models.BooleanField(default=False, help_text='Send as HTML email')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='NotificationLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('recipient', models.CharField(max_length=255)),
                ('subject', models.CharField(blank=True, max_length=255)),
                ('message', models.TextField()),
                ('parameters', models.JSONField(default=dict)),
                ('status', models.CharField(
                    choices=[('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed')],
                    default='PENDING', max_length=20,
                )),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('template', models.ForeignKey(
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to='api.notificationtemplate',
                )),
            ],
            options={'ordering': ['-created_at']},
        ),
    ]
