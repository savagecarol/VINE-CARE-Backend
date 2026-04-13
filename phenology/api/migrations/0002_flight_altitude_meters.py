from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='flight',
            name='altitude_meters',
            field=models.IntegerField(blank=True, null=True, help_text='Drone flight altitude in meters (e.g. 100, 120, 140)'),
        ),
    ]
