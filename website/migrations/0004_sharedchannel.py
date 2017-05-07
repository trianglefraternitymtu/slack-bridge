# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-07 19:04
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('website', '0003_remove_team_webhook_url'),
    ]

    operations = [
        migrations.CreateModel(
            name='SharedChannel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('channel_id', models.CharField(max_length=12)),
                ('local_team', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='website.Team')),
            ],
        ),
    ]
