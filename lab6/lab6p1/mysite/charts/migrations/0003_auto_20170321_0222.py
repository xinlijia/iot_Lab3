# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-21 02:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('charts', '0002_auto_20170320_1112'),
    ]

    operations = [
        migrations.AddField(
            model_name='chart',
            name='floattime',
            field=models.DecimalField(decimal_places=3, default=0, max_digits=13),
        ),
        migrations.AlterField(
            model_name='chart',
            name='temp',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
    ]
