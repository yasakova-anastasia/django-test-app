# Generated by Django 4.2.3 on 2023-07-20 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tournament', '0001_initial'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='hinttaken',
            constraint=models.UniqueConstraint(fields=('task', 'team'), name='unique_hint_taken'),
        ),
    ]
