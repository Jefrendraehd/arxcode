# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2018-07-02 23:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dominion', '0026_rpevent_risk'),
    ]

    operations = [
        migrations.CreateModel(
            name='Honorific',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(db_index=True, max_length=200)),
                ('description', models.TextField()),
                ('amount', models.IntegerField(default=0)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='honorifics', to='dominion.AssetOwner')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Propriety',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=120, unique=True)),
                ('percentage', models.SmallIntegerField(default=0)),
                ('owners', models.ManyToManyField(related_name='proprieties', to='dominion.AssetOwner')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
