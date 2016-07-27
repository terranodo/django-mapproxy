import logging
import helpers
from pyproj import Proj, transform

from django.db import models
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from guardian.shortcuts import assign_perm
from mapproxy.seed.config import SeedConfigurationError, ConfigurationError

log = logging.getLogger('djmapproxy')

CACHE_TYPES = [
    ['file', 'file'],
    #['mbtiles','mbtiles'],
    #['sqllite', 'sqllite'],
    ['geopackage', 'geopackage']
]

DIR_LAYOUTS = [
    ['tms', 'tms'],
    ['tc', 'TileCache']
]

SOURCE_TYPES = [
    ['wms','wms'],
    ['tile', 'tile'],
    ['mapnik', 'mapnik']
]

class Tileset(models.Model):
    # base
    name = models.CharField(max_length=255)
    created_by = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    source_type = models.CharField(max_length=10, choices=SOURCE_TYPES)


    # server
    server_url = models.URLField(blank=True, null=True)
    server_username = models.CharField(blank=True, null=True, max_length=30)
    server_password = models.CharField(blank=True, null=True, max_length=30)

    # layer
    layer_name = models.CharField(blank=True, null=True, max_length=200)
    layer_zoom_start = models.IntegerField(default=0)
    layer_zoom_stop = models.IntegerField(default=12)

    # area
    bbox_x0 = models.DecimalField(max_digits=19, decimal_places=15, default=-180, validators = [MinValueValidator(-180), MaxValueValidator(180)])
    bbox_x1 = models.DecimalField(max_digits=19, decimal_places=15, default=180, validators = [MinValueValidator(-180), MaxValueValidator(180)])
    bbox_y0 = models.DecimalField(max_digits=19, decimal_places=15, default=-89.9, validators = [MinValueValidator(-89.9), MaxValueValidator(89.9)])
    bbox_y1 = models.DecimalField(max_digits=19, decimal_places=15, default=89.9, validators = [MinValueValidator(-89.9), MaxValueValidator(89.9)])

    # cache
    cache_type = models.CharField(max_length=10, choices=CACHE_TYPES)
    # file cache params
    directory_layout = models.CharField(max_length=20, choices=DIR_LAYOUTS, blank=True, null=True)
    directory = models.CharField(max_length=256, default=settings.TILESET_CACHE_DIRECTORY, blank=True, null=True)
    # gpkg cache params
    filename = models.CharField(max_length=256, blank=True, null=True)
    table_name = models.CharField(max_length=128, blank=True, null=True)

    # mapnik params
    mapfile = models.FileField(blank=True, null=True, upload_to='mapfiles')

    # geonode params
    layer_uuid = models.CharField(max_length=36, null=True, blank=True)

    # size
    size = models.CharField('Size (MB)', default='0', max_length=128)

    def __unicode__(self):
        return self.name

    # terminate the seeding of this tileset!
    def stop(self):
        log.debug('tileset.stop')
        res = {'status': 'not in progress'}
        pid_str = helpers.get_pid_from_lock_file(self)
        process = helpers.get_process_from_pid(pid_str)
        if process:
            log.debug('tileset.stop, will stop, pid: {}').format(pid_str)
            res = {'status': 'stopped'}
            children = process.children()
            for c in children:
                c.terminate()
            process.terminate()
        else:
            if pid_str == 'preparing_to_start':
                res = {'status': 'debug, prevent start!'}
                # TODO: prevent it from starting!
                log.debug('process not running but may be started shortly')
            elif helpers.is_int_str(pid_str):
                log.debug('tileset.stop, process not running but cleaned lock file')

        helpers.remove_lock_file(self.id)
        return res

    def seed(self):
        
        lock_file = helpers.get_lock_file(self)
        if lock_file:
            log.debug('generating tileset')
            try:
                pid = helpers.seed_process_spawn(self)
                lock_file.write("{}\n".format(pid))
                res = {'status': 'started'}
            except (SeedConfigurationError, ConfigurationError) as e:
                log.error('Something went wrong when generating.. removing lock file')
                res = {'status': 'unable to start',
                       'error': e.message}
            finally:
                lock_file.flush()
                lock_file.close()
                helpers.remove_lock_file(self)
        else:
            log.debug('tileset.generate, will NOT generate. already running, pid: {}'.format(helpers.get_pid_from_lock_file(self)))
            res = {'status': 'already started'}

        return res

    def bbox_3857(self):
        inProj = Proj(init='epsg:4326')
        outProj = Proj(init='epsg:3857')

        sw = transform(inProj, outProj, self.bbox_x0, self.bbox_y0)
        ne = transform(inProj, outProj, self.bbox_x1, self.bbox_y1)

        return [sw[0], sw[1], ne[0], ne[1]]

    def bbox(self):
        return [self.bbox_x0, self.bbox_y0, self.bbox_x1, self.bbox_y1]

    def add_read_perm(self, user_or_group):
        return assign_perm('view_tileset', user_or_group, self)

    def set_up_permissions(self, user_or_group=None):
        # TODO(mvv): handle default anonymous permissions

        if user_or_group:
            self.add_read_perm(user_or_group)

    class Meta:
        permissions = (
            ('view_tileset', 'View Tileset'),
        )
