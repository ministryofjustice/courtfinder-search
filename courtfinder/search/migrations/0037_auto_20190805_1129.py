# -*- coding: utf-8 -*-
# Generated by Django 1.11.22 on 2019-08-05 11:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0036_court_name_cy'),
    ]

    operations = [
        migrations.AddField(
            model_name='areaoflaw',
            name='alt_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='areaoflaw',
            name='alt_name_cy',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
