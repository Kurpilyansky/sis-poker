# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-08-04 23:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0007_carddeck_dealer_error'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carddeck',
            name='dealer_error',
            field=models.IntegerField(default=0, help_text='маска ошибок дилера'),
        ),
    ]
