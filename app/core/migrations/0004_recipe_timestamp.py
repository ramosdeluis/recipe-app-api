# Generated by Django 3.2.19 on 2023-06-30 13:27

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_recipe_difficulty'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
