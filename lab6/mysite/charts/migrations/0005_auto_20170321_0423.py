# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-21 04:23
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charts', '0004_auto_20170321_0356'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chart',
            name='timestamp',
            field=models.CharField(default='Null', max_length=100),
        ),
    ]
