# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-16 14:03
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0002_auto_20170716_1320'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='name',
            field=models.CharField(default='', max_length=500),
            preserve_default=False,
        ),
    ]