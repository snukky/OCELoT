# Generated by Django 3.1.7 on 2021-06-16 09:34
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):
    dependencies = [
        ('leaderboard', '0030_auto_20210615_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='description',
            field=models.TextField(
                blank=True,
                help_text='Team description (max 2000 characters)',
                max_length=2000,
            ),
        ),
        migrations.AddField(
            model_name='team',
            name='publication_url',
            field=models.CharField(
                blank=True,
                help_text='Publication URL or citation',
                max_length=200,
            ),
        ),
    ]
