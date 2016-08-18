import json
import logging
import os
import tempfile
import time

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from django.views import generic
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponse
from guardian.decorators import permission_required_or_403
from mapproxy.config.config import load_default_config, load_config
from mapproxy.util.ext.dictspec.validator import validate, ValidationError
from mapproxy.config.loader import ProxyConfiguration, ConfigurationError
from mapproxy.wsgiapp import MapProxyApp
from webtest import TestApp as TestApp_
import yaml

from .decorators import view_tileset_permissions
from .models import Tileset
from .helpers import get_status, generate_confs
from .validator import validate_references, validate_options

log = logging.getLogger('mapproxy.config')


class DetailView(generic.DetailView):
    model = Tileset
    template_name = 'djmp/tileset_detail.html'


@login_required
@view_tileset_permissions
def seed(request, pk):
    tileset = get_object_or_404(Tileset, pk=pk)
    return HttpResponse(json.dumps(tileset.seed()))


@login_required
@view_tileset_permissions
def tileset_status(request, pk):
    tileset = get_object_or_404(Tileset, pk=pk)
    return HttpResponse(json.dumps(get_status(tileset)))


class TestApp(TestApp_):
    """
    Wraps webtest.TestApp and explicitly converts URLs to strings.
    Behavior changed with webtest from 1.2->1.3.
    """
    def get(self, url, *args, **kw):
        kw['expect_errors'] = True
        return TestApp_.get(self, str(url), *args, **kw)


def simple_name(layer_name):
    layer_name = str(layer_name)

    if ':' in layer_name:
        layer_name = layer_name.split(':')[1]

    return layer_name


def get_mapproxy(tileset):
    """Creates a mapproxy config for a given layer-like object.
       Compatible with django-registry and GeoNode.
    """
    
    mapproxy_cf, seed_cf = generate_confs(tileset)

    # Create a MapProxy App
    app = MapProxyApp(mapproxy_cf.configured_services(), mapproxy_cf.base_config)

    # Wrap it in an object that allows to get requests by path as a string.
    return TestApp(app), mapproxy_cf


@view_tileset_permissions
def tileset_mapproxy(request, pk, path_info):
    # TODO(mvv): this could be handled as a decorator or some 
    #            other more generalizable pattern

    tileset = get_object_or_404(Tileset, pk=pk)
    mp, yaml_config = get_mapproxy(tileset)

    query = request.META['QUERY_STRING']

    if len(query) > 0:
        path_info = path_info + '?' + query

    params = {}
    headers = {
       'X-Script-Name': str(request.get_full_path()),
       'X-Forwarded-Host': request.META['HTTP_HOST'],
       'HTTP_HOST': request.META['HTTP_HOST'],
       'SERVER_NAME': request.META['SERVER_NAME'],
    }

    if path_info == '/config':
        response = HttpResponse(yaml_config, content_type='text/plain')
        return response

    # Get a response from MapProxy as if it was running standalone.
    mp_response = mp.get(path_info, params, headers)

    if mp_response.status_code == 500:
        raise Exception('map proxy exception occurred: %s' % (mp_response,))

    # Create a Django response from the MapProxy WSGI response.
    response = HttpResponse(mp_response.body, status=mp_response.status_int)
    for header, value in mp_response.headers.iteritems():
        response[header] = value

    return response
