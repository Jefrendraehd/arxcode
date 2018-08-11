# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-11-09 08:16
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('msgs', '0006_remove_inform_read_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='inform',
            name='read_by',
            field=models.ManyToManyField(blank=True, related_name='read_informs', to=settings.AUTH_USER_MODEL),
        ),
    ]
