# -*- coding: utf-8 -*-
# Generated by Django 1.11.28 on 2020-05-28 14:22
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0037_auto_20190805_1129'),
    ]

    operations = [
        migrations.AddField(
            model_name='court',
            name='gbs',
            field=models.TextField(blank=True, null=True),
        ),
    ]
