from django.conf import settings
from mapproxy.seed.seeder import seed
from mapproxy.seed.config import SeedingConfiguration, SeedConfigurationError, ConfigurationError
from mapproxy.seed.spec import validate_seed_conf
from mapproxy.config.loader import ProxyConfiguration
#from mapproxy.config.spec import validate_mapproxy_conf
from mapproxy.seed import seeder
from mapproxy.seed import util
from django.utils.text import slugify

from datetime import datetime
import base64
import yaml
import os
import errno
import time
from dateutil import parser
import multiprocessing
import psutil
import logging

from .settings import CACHE_CONFIG
from .conf_templates import mapproxy_conf, seed_conf

log = logging.getLogger('djmapproxy')


def generate_confs(tileset, ignore_warnings=True, renderd=False):
    """
    Takes a Tileset object and returns mapproxy and seed config files
    """

    mapproxy_conf = yaml.safe_load(mapproxy_conf.format({
        'layer_name': tileset.layer_name,
        'layer_title': tileset.layer_title,
        'tileset_source_type': u_to_str(tileset.server_service_type)
        }))

    seed_conf = yaml.safe_load(seed_conf.format({
        'seed_zoom_start': tileset.layer_zoom_start,
        'seed_zoom_stop': tileset.layer_zoom_stop
        }))
    

    log.debug('cache to generate: {}'.format(get_tileset_filename(tileset.name))

    server_service_type = u_to_str(tileset.server_service_type)

    if server_service_type == 'wms':
        mapproxy_conf['sources']['tileset_source']['req'] = {}
        mapproxy_conf['sources']['tileset_source']['req']['url'] = u_to_str(tileset.server_url)
        mapproxy_conf['sources']['tileset_source']['req']['layers'] = u_to_str(tileset.layer_name)
        mapproxy_conf['sources']['tileset_source']['req']['transparent'] = 'true'
   
    elif server_service_type == 'tile':
        mapproxy_conf['sources']['tileset_source']['url'] = u_to_str(tileset.server_url)

    mapproxy_conf['layers'][0]['name'] = u_to_str(tileset.layer_name)
    mapproxy_conf['layers'][0]['title'] = u_to_str(tileset.layer_name)
    mapproxy_conf['caches']['tileset_cache']['cache']['filename'] = get_tileset_filename(tileset.name, 'generating')
    mapproxy_conf['caches']['tileset_cache']['cache']['table_name'] = str(slugify(tileset.name).replace('-', '_'))

    if tileset.layer_zoom_start > tileset.layer_zoom_stop:
        raise ConfigurationError('invalid configuration - zoom start is greater than zoom stop')
    seed_conf['seeds']['tileset_seed']['levels']['from'] = tileset.layer_zoom_start
    seed_conf['seeds']['tileset_seed']['levels']['to'] = tileset.layer_zoom_stop
    
    # any specified refresh before for gpkg will result in regeneration of the tile set
    seed_conf['seeds']['tileset_seed']['refresh_before']['minutes'] = 0
    
    bbox = [tileset.x0, tileset.y0, tileset.x1, tileset.y1]
    seed_conf['coverages']['tileset_geom']['bbox'] = yaml.safe_load(bbox)

    if tileset.server_username and tileset.server_password:

        encoded = base64.b64encode('{}:{}'.format(tileset.server_username, tileset.server_password))
        mapproxy_conf['sources']['tileset_source']['http'] = {}
        mapproxy_conf['sources']['tileset_source']['http']['headers'] = {}
        mapproxy_conf['sources']['tileset_source']['http']['headers']['Authorization'] = 'Basic {}'.format(encoded)
        mapproxy_conf['sources']['tileset_source']['http']['ssl_no_cert_checks'] = True

    """
    errors, informal_only = validate_mapproxy_conf(mapproxy_conf)
    for error in errors:
        print error
    if not informal_only or (errors and not ignore_warnings):
        raise ConfigurationError('invalid configuration - {}'.format(', '.join(errors)))
    """
    cf = ProxyConfiguration(mapproxy_conf, seed=seed, renderd=renderd)

    errors, informal_only = validate_seed_conf(seed_conf)
    for error in errors:
        print error
    if not informal_only:
        raise SeedConfigurationError('invalid seed configuration - {}'.format(', '.join(errors)))
    seed_cf = SeedingConfiguration(seed_conf, mapproxy_conf=cf)

    return cf, seed_cf


"""
example settings file
TILEBUNDLER_CONFIG = {
    'tileset_dir': '/var/lib/gpkg'
}
"""
def get_tileset_dir():
    conf = getattr(settings, 'CACHE_CONFIG', {})
    return conf.get('directory', './')


def get_tileset_filename(tileset_name, extension='gpkg'):
    return '{}/{}.{}'.format(get_tileset_dir(), tileset_name, extension)


def get_lock_filename(tileset_id):
    return '{}/generate_tileset_{}.lck'.format(get_tileset_dir(), tileset_id)


def update_tileset_stats(tileset):
    tileset_filename = get_tileset_filename(tileset.name)
    if os.path.isfile(tileset_filename):
        stat = os.stat(tileset_filename)
        tileset.created_at = datetime.fromtimestamp(stat.st_ctime)
        tileset.filesize = stat.st_size
        tileset.save()


def u_to_str(string):
    return string.encode('ascii', 'ignore')


def is_int_str(v):
    v = str(v).strip()
    return v == '0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()


def add_tileset_file_attribs(target_object, tileset, extension='gpkg'):
    tileset_filename = get_tileset_filename(tileset.name, extension)
    if os.path.isfile(tileset_filename):
        stat = os.stat(tileset_filename)
        if stat:
            target_object['file_size'] = stat.st_size
            target_object['file_updated'] = datetime.fromtimestamp(stat.st_ctime)


def get_status(tileset):
    res = {
        'current': {
            'status': 'unknown'
        },
        'pending': {
            'status': 'not in progress'
        }
    }

    # generate status for already existing tileset
    # if there is a .gpkg file on disk, get the size and time last updated
    tileset_filename = get_tileset_filename(tileset.name)
    if os.path.isfile(tileset_filename):
        res['current']['status'] = 'ready'
        # get the size and time last updated for the tileset
        add_tileset_file_attribs(res['current'], tileset)
    else:
        res['current']['status'] = 'not generated'

    # get the size and time last updated for the 'pending' tileset
    add_tileset_file_attribs(res['pending'], tileset, 'generating')

    pid = get_pid_from_lock_file(tileset.id)
    if pid:
        process = get_is_process_running(pid)
        if process:
            # if tileset generation is in progress
            res['pending']['status'] = 'in progress'
            progress_log_filename = get_tileset_filename(tileset.name, 'progress_log')
            if os.path.isfile(progress_log_filename):
                with open(progress_log_filename, 'r') as f:
                    lines = f.read().replace('\r', '\n')
                    lines = lines.split('\n')

                # an actual progress step update which looks like:
                # "[15:11:11]  4  50.00% 0.00000, 672645.84891, 18432942.24503, 18831637.78456 (112 tiles) ETA: 2015-07-07-15:11:12"\n
                latest_step = None
                # a progress update on the current step which looks like:
                # "[15:11:16]  87.50%   0000                 ETA: 2015-07-07-15:11:17'\r
                latest_progress = None
                if len(lines) > 0:
                    for line in lines[::-1]:
                        tokens = line.split()
                        if len(tokens) > 2:
                            if is_int_str(tokens[1]):
                                latest_step = tokens
                                break
                            elif tokens[1].endswith('%'):
                                if latest_progress is None:
                                    # keep going, don't break
                                    latest_progress = tokens
                                    continue
                if latest_step:
                    # if we have a step %, up date the progress %
                    if latest_progress:
                        latest_step[2] = latest_progress[1]

                    res['pending']['progress'] = latest_step[2][0:-1]
                    res['pending']['current_zoom_level'] = latest_step[1]

                    # get the eta but pass if date is cannot be parsed.
                    try:
                        iso_date = parser.parse(latest_step[len(latest_step) - 1]).isoformat()
                        res['pending']['estimated_completion_time'] = iso_date
                    except ValueError:
                        pass
            else:
                res['pending']['status'] = 'in progress, but log not found'
        else:
            res['pending']['status'] = 'stopped'
    return res
    

# when using uwsgi, several processes each with their own interpreter are often launched. This means that the typical
# multiprocessing sync mechanisms such as Lock and Manager cannot be used. comments about issues to know about uwsgi:
# http://uwsgi-docs.readthedocs.org/en/latest/ThingsToKnow.html note that enable-threads, close-on-exec, and
# close-on-exec2 were not effective and even if they were, other deployments will need to match uwsgi setting which is
# inconvenient especially since the problems caused can be misleading. The implementation here uses lock files to check
# if a tileset is being generated and which process to kill when generate needs to be stopped by a user. Using celery
# for multiprocessing poses another problem: since it generates its worker pool processes as proc.daemon = True,
# each celery process cannot invoke the mapproxy.seed function which in turn wants to launch other processes. This
# can be fixed in celery but it requires a patch. celery project reopened this 'bug' a few days ago as of 7-22-2015:
# https://github.com/celery/celery/issues/1709 if it is fixed, we can switch to using celery without any immediate
# gain for the current use case. Instead of using daemon processes, they should use another mechanism to track/kill
# child processes so that each celery task can launch other processes.
def seed_process_spawn(tileset):
    mapproxy_conf, seed_conf = generate_confs(tileset)

    # if there is an old _generating one around, back it up
    backup_millis = int(round(time.time() * 1000))
    if os.path.isfile(get_tileset_filename(tileset.name, 'generating')):
        os.rename(get_tileset_filename(tileset.name, 'generating'), '{}_{}'.format(get_tileset_filename(tileset.name, 'generating'), backup_millis))

    # if there is an old progress_log around, back it up
    if os.path.isfile(get_tileset_filename(tileset.name, 'progress_log')):
        os.rename(get_tileset_filename(tileset.name, 'progress_log'), '{}_{}'.format(get_tileset_filename(tileset.name, 'generating'), backup_millis))

    # generate the new gpkg as name.generating file
    progress_log_filename = get_tileset_filename(tileset.name, 'progress_log')
    out = open(progress_log_filename, 'w+')
    progress_logger = util.ProgressLog(out=out, verbose=True, silent=False)
    tasks = seed_conf.seeds(['tileset_seed'])
    # launch the task using another process
    process = multiprocessing.Process(target=seed_process_target, args=(tileset.id, tileset.name, tasks, progress_logger))
    pid = None
    if 'preparing_to_start' == get_pid_from_lock_file(tileset.id):
        process.start()
        pid = process.pid
    else:
        print '---- Not starting process. cancel was requested. '
    return pid


def seed_process_target(tileset_id, tileset_name, tasks, progress_logger):
    print '----[ start seeding. tileset {}'.format(tileset_id)
    seeder.seed(tasks=tasks, progress_logger=progress_logger)

    # now that we have generated the new gpkg file, backup the last one, then rename
    # the _generating one to the main name
    if os.path.isfile(get_tileset_filename(tileset_name)):
        millis = int(round(time.time() * 1000))
        os.rename(get_tileset_filename(tileset_name), '{}_{}'.format(get_tileset_filename(tileset_name), millis))
    os.rename(get_tileset_filename(tileset_name, 'generating'), get_tileset_filename(tileset_name))
    remove_lock_file(tileset_id)


def get_lock_file(tileset_id):
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    lock_file = None

    try:
        file_handle = os.open(get_lock_filename(tileset_id), flags)
    except OSError as e:
        if e.errno == errno.EEXIST:
            # Failed, file already exists.
            pass
        else:
            # Something unexpected went wrong so re-raise the exception.
            raise
    else:
        # No exception, so the file must have been created successfully.
        lock_file = os.fdopen(file_handle, 'w')
        lock_file.write('preparing_to_start\n')
        lock_file.flush()
    return lock_file


def remove_lock_file(tileset_id):
    try:
        os.remove(get_lock_filename(tileset_id))
    except OSError as e:
        # Error removing lock file
        print '--- There was a problem removing the lock file. Something: {}'.format(e.errno)
        pass


def get_pid_from_lock_file(tileset_id):
    pid = None
    name = get_lock_filename(tileset_id)
    if os.path.isfile(name):
        with open(name, 'r') as lock_file:
            lines = lock_file.readlines()
            if len(lines) > 0:
                if lines[-1]:
                    pid = lines[-1].rstrip()
    return pid


def get_process_from_pid(pid):
    process = None
    if is_int_str(pid):
        try:
            process = psutil.Process(pid=int(pid))
        except (psutil.NoSuchProcess, psutil.ZombieProcess):
            print ' -- PROCESS HAS BEEN TERMINATED {}'.format(int(pid))
            pass
    return process

def get_is_process_running(pid):
    process = None
    if is_int_str(pid):
        try:
            process = psutil.Process(pid=int(pid))
            exitCode = process.wait(0)
            print ' -- waited for process.. exitCode: {}'.format(exitCode)
        except (psutil.NoSuchProcess, psutil.ZombieProcess, psutil.TimeoutExpired):
            pass
    return process
