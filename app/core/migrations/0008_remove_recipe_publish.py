# Generated by Django 3.2.19 on 2023-06-30 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_recipe_publish'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recipe',
            name='publish',
        ),
    ]
