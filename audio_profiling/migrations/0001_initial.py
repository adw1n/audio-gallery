# -*- coding: utf-8 -*-
# Generated by Django 1.10.6 on 2017-04-29 13:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AudioFile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, unique=True)),
                ('audio_file', models.FileField(upload_to='files/songs/%Y/%m/%d')),
                ('waveform', models.FileField(blank=True, editable=False, null=True, upload_to='files/waveforms')),
                ('mp3', models.FileField(blank=True, editable=False, null=True, upload_to='files/songs/%Y/%m/%d')),
                ('spectrogram', models.FileField(blank=True, editable=False, null=True, upload_to='files/spectrograms')),
                ('spectrum', models.FileField(blank=True, editable=False, null=True, upload_to='files/spectrums')),
                ('start_page', models.BooleanField(default=False)),
                ('TOP_IMG_MARGIN', models.IntegerField(blank=True, editable=False, null=True)),
                ('BOTTOM_IMG_MARGIN', models.IntegerField(blank=True, editable=False, null=True)),
                ('RIGHT_IMG_MARGIN', models.IntegerField(blank=True, editable=False, null=True)),
                ('LEFT_IMG_MARGIN', models.IntegerField(blank=True, editable=False, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='AudioPage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('name_pl', models.CharField(max_length=100, null=True)),
                ('photo', models.ImageField(blank=True, null=True, upload_to='files/photos/%Y/%m/%d')),
                ('description', models.TextField(blank=True)),
                ('description_en', models.TextField(blank=True, null=True)),
                ('description_pl', models.TextField(blank=True, null=True)),
                ('page_number', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('name_en', models.CharField(max_length=100, null=True)),
                ('name_pl', models.CharField(max_length=100, null=True)),
                ('parent_category', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='audio_profiling.Category')),
            ],
            options={
                'verbose_name_plural': 'Categories',
            },
        ),
        migrations.AddField(
            model_name='audiopage',
            name='categories',
            field=models.ManyToManyField(blank=True, to='audio_profiling.Category'),
        ),
        migrations.AddField(
            model_name='audiofile',
            name='audio_page',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='audio_profiling.AudioPage'),
        ),
        migrations.AddField(
            model_name='audiofile',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='audio_profiling.Category'),
        ),
    ]