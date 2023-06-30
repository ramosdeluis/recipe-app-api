# Generated by Django 3.2.19 on 2023-06-30 11:40

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_ingredient_amount'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='difficulty',
            field=models.PositiveSmallIntegerField(default=0, validators=[django.core.validators.MaxValueValidator(5)]),
        ),
    ]