import logging

from django.db import models
from django.conf import settings
from mapproxy.seed.config import SeedConfigurationError, ConfigurationError
import helpers

log = logging.getLogger('djmapproxy')

class Tileset(models.Model):

    # base
    name = models.CharField(unique=True, max_length=30)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # server
    server_url = models.URLField()
    server_service_type = models.CharField(max_length=10)
    server_username = models.CharField(blank=True, max_length=30)
    server_password = models.CharField(blank=True, max_length=30)

    # layer
    layer_name = models.CharField(blank=True, max_length=200)
    layer_zoom_start = models.IntegerField(blank=True, default=0)
    layer_zoom_stop = models.IntegerField()

    # area
    bbox_x0 = models.DecimalField(max_digits=19, decimal_places=10, default=-180)
    bbox_x1 = models.DecimalField(max_digits=19, decimal_places=10, default=-90)
    bbox_y0 = models.DecimalField(max_digits=19, decimal_places=10, default=180)
    bbox_y1 = models.DecimalField(max_digits=19, decimal_places=10, default=90)

    def __unicode__(self):
        return self.name

    # terminate the seeding of this tileset!
    def stop(self):
        log.debug('tileset.stop')
        res = {'status': 'not in progress'}
        pid_str = helpers.get_pid_from_lock_file(self.id)
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
                log.debug('tileset.stop, process not running but cleaned lck file')

        helpers.remove_lock_file(self.id)
        return res

    def seed(self):
        
        lock_file = helpers.get_lock_file(self.id)
        if lock_file:
            log.debug('generating tileset')
            try:
                pid = helpers.seed_process_spawn(self)
                lock_file.write("{}\n".format(pid))
                res = {'status': 'started'}
            except (SeedConfigurationError, ConfigurationError) as e:
                log.error('Something went wrong when generating.. removing lock file')

                helpers.remove_lock_file(self.id)
                res = {'status': 'unable to start',
                       'error': e.message}
            finally:
                lock_file.flush()
                lock_file.close()
        else:
            log.debug('tileset.generate, will NOT generate. already running, pid: {}'.format(helpers.get_pid_from_lock_file(self.id)))
            res = {'status': 'already started'}

        return res
