# -*- coding: utf-8 -*-
# Generated by Django 1.9.9 on 2017-02-09 02:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('character', '0007_auto_20170130_1437'),
    ]

    operations = [
        migrations.AddField(
            model_name='investigation',
            name='action_points',
            field=models.PositiveSmallIntegerField(blank=0, default=0, help_text=b'How many action points spent by player/assistants.'),
        ),
        migrations.AddField(
            model_name='rosterentry',
            name='action_points',
            field=models.SmallIntegerField(blank=100, default=100),
        ),
    ]
