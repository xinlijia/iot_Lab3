# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-03-21 01:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('p2', '0002_auto_20170321_0049'),
    ]

    operations = [
        migrations.AddField(
            model_name='city',
            name='temp',
            field=models.FloatField(default=0),
        ),
    ]
