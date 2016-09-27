# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Tileset',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('created_by', models.CharField(max_length=256)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('source_type', models.CharField(max_length=10, choices=[[b'wms', b'wms'], [b'tile', b'tile'], [b'mapnik', b'mapnik']])),
                ('server_url', models.URLField(null=True, blank=True)),
                ('server_username', models.CharField(max_length=30, null=True, blank=True)),
                ('server_password', models.CharField(max_length=30, null=True, blank=True)),
                ('layer_name', models.CharField(max_length=200, null=True, blank=True)),
                ('layer_zoom_start', models.IntegerField(default=0)),
                ('layer_zoom_stop', models.IntegerField(default=12)),
                ('bbox_x0', models.DecimalField(default=-180, max_digits=19, decimal_places=15, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)])),
                ('bbox_x1', models.DecimalField(default=180, max_digits=19, decimal_places=15, validators=[django.core.validators.MinValueValidator(-180), django.core.validators.MaxValueValidator(180)])),
                ('bbox_y0', models.DecimalField(default=-89.9, max_digits=19, decimal_places=15, validators=[django.core.validators.MinValueValidator(-89.9), django.core.validators.MaxValueValidator(89.9)])),
                ('bbox_y1', models.DecimalField(default=89.9, max_digits=19, decimal_places=15, validators=[django.core.validators.MinValueValidator(-89.9), django.core.validators.MaxValueValidator(89.9)])),
                ('cache_type', models.CharField(max_length=10, choices=[[b'file', b'file'], [b'geopackage', b'geopackage']])),
                ('directory_layout', models.CharField(blank=True, max_length=20, null=True, choices=[[b'tms', b'tms'], [b'tc', b'TileCache']])),
                ('directory', models.CharField(default=b'/Users/ortelius/projects/nga-dev/django-mapproxy/cache/layers', max_length=256, null=True, blank=True)),
                ('filename', models.CharField(max_length=256, null=True, blank=True)),
                ('table_name', models.CharField(max_length=128, null=True, blank=True)),
                ('mapfile', models.FileField(null=True, upload_to=b'mapfiles', blank=True)),
                ('layer_uuid', models.CharField(max_length=36, null=True, blank=True)),
                ('size', models.CharField(default=b'0', max_length=128, verbose_name=b'Size (MB)')),
            ],
            options={
                'permissions': (('view_tileset', 'View Tileset'),),
            },
        ),
    ]
