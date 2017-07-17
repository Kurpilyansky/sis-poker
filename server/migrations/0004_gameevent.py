# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-17 14:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0003_table_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='GameEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deck_id', models.IntegerField()),
                ('player_id', models.IntegerField(blank=True, null=True)),
                ('player_name', models.CharField(blank=True, max_length=100, null=True)),
                ('event_id', models.IntegerField()),
                ('event_type', models.CharField(max_length=500)),
                ('args', models.CharField(max_length=2000)),
                ('table', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='server.Table')),
            ],
        ),
    ]
