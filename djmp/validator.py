# This file is part of the MapProxy project.
# Copyright (C) 2015 Omniscale <http://omniscale.de>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

import datetime
import os.path
from mapproxy.compat import string_type, iteritems
from mapproxy.util.ext.dictspec.validator import validate, ValidationError
from mapproxy.util.ext.dictspec.spec import one_of, anything, number
from mapproxy.util.ext.dictspec.spec import recursive, required, type_spec, combined
from mapproxy.compat import string_type

import logging
log = logging.getLogger('mapproxy.config')


TAGGED_SOURCE_TYPES = [
    'wms',
    'mapserver',
    'mapnik'
]


def validate_references(conf_dict):
    validator = Validator(conf_dict)
    return validator.validate()


grids = dict(
    GLOBAL_GEODETIC=dict(
        srs='EPSG:4326', origin='sw', name='GLOBAL_GEODETIC'
    ),
    GLOBAL_MERCATOR=dict(
        srs='EPSG:900913', origin='sw', name='GLOBAL_MERCATOR'
    ),
    GLOBAL_WEBMERCATOR=dict(
        srs='EPSG:3857', origin='nw', name='GLOBAL_WEBMERCATOR'
    )
)

class Validator(object):

    def __init__(self, conf_dict):
        self.sources_conf = conf_dict.get('sources', {})
        self.caches_conf = conf_dict.get('caches', {})
        self.layers_conf = conf_dict.get('layers')
        self.services_conf = conf_dict.get('services')
        self.grids_conf = conf_dict.get('grids')
        self.globals_conf = conf_dict.get('globals')

        self.errors = []
        self.known_grids = set(grids.keys())
        if self.grids_conf:
            self.known_grids.update(self.grids_conf.keys())

    def validate(self):
        if not self.layers_conf:
            self.errors.append("Missing layers section")
        if isinstance(self.layers_conf, dict):
            return []
        if not self.services_conf:
            self.errors.append("Missing services section")

        if len(self.errors) > 0:
            return self.errors

        for layer in self.layers_conf:
            self._validate_layer(layer)

        return self.errors

    def _validate_layer(self, layer):
        layer_sources = layer.get('sources', [])
        tile_sources = layer.get('tile_sources', [])
        child_layers = layer.get('layers', [])

        if not layer_sources and not child_layers and not tile_sources:
            self.errors.append(
                "Missing sources for layer '%s'" % layer.get('name')
            )
        for child_layer in child_layers:
            self._validate_layer(child_layer)

        for source in layer_sources:
            if source in self.caches_conf:
                self._validate_cache(source, self.caches_conf[source])
                continue
            if source in self.sources_conf:
                source, layers = self._split_tagged_source(source)
                self._validate_source(source, self.sources_conf[source], layers)
                continue

            self.errors.append(
                "Source '%s' for layer '%s' not in cache or source section" % (
                    source,
                    layer['name']
                )
            )

        for source in tile_sources:
            if source in self.caches_conf:
                self._validate_cache(source, self.caches_conf[source])
                continue

            self.errors.append(
                "Tile source '%s' for layer '%s' not in cache section" % (
                    source,
                    layer['name']
                )
            )


    def _split_tagged_source(self, source_name):
        layers = None
        if ':' in str(source_name):
            source_name, layers = str(source_name).split(':')
            layers = layers.split(',') if layers is not None else None
        return source_name, layers

    def _validate_source(self, name, source, layers):
        source_type = source.get('type')
        if source_type == 'wms':
            self._validate_wms_source(name, source, layers)
        if source_type == 'mapserver':
            self._validate_mapserver_source(name, source, layers)
        if source_type == 'mapnik':
            self._validate_mapnik_source(name, source, layers)

    def _validate_wms_source(self, name, source, layers):
        if source['req'].get('layers') is None and layers is None:
            self.errors.append("Missing 'layers' for source '%s'" % (
                name
            ))
        if source['req'].get('layers') is not None and layers is not None:
            self._validate_tagged_layer_source(
                name,
                source['req'].get('layers'),
                layers
            )

    def _validate_mapserver_source(self, name, source, layers):
        mapserver = source.get('mapserver')
        if mapserver is None:
            if (
                not self.globals_conf or
                not self.globals_conf.get('mapserver') or
                not self.globals_conf['mapserver'].get('binary')
            ):
                self.errors.append("Missing mapserver binary for source '%s'" % (
                    name
                ))
            elif not os.path.isfile(self.globals_conf['mapserver']['binary']):
                self.errors.append("Could not find mapserver binary (%s)" % (
                    self.globals_conf['mapserver'].get('binary')
                ))
        elif mapserver is None or not source['mapserver'].get('binary'):
            self.errors.append("Missing mapserver binary for source '%s'" % (
                name
            ))
        elif not os.path.isfile(source['mapserver']['binary']):
            self.errors.append("Could not find mapserver binary (%s)" % (
                source['mapserver']['binary']
            ))

        if source['req'].get('layers') and layers is not None:
            self._validate_tagged_layer_source(
                name,
                source['req'].get('layers'),
                layers
            )

    def _validate_mapnik_source(self, name, source, layers):
        if source.get('layers') and layers is not None:
            self._validate_tagged_layer_source(name, source.get('layers'), layers)

    def _validate_tagged_layer_source(self, name, supported_layers, requested_layers):
        if isinstance(supported_layers, string_type):
            supported_layers = [supported_layers]
        if not set(requested_layers).issubset(set(supported_layers)):
            self.errors.append(
                "Supported layers for source '%s' are '%s' but tagged source requested "
                "layers '%s'" % (
                    name,
                    ', '.join(supported_layers),
                    ', '.join(requested_layers)
                ))

    def _validate_cache(self, name, cache):
        if isinstance(cache.get('sources', []), dict):
            self._validate_bands(name, set(cache['sources'].keys()))
            for band, confs  in iteritems(cache['sources']):
                for conf in confs:
                    band_source = conf['source']
                    self._validate_cache_source(name, band_source)
        else:
            for cache_source in cache.get('sources', []):
                self._validate_cache_source(name, cache_source)

        for grid in cache.get('grids', []):
            if grid not in self.known_grids:
                self.errors.append(
                    "Grid '%s' for cache '%s' not found in config" % (
                        grid,
                        name
                    )
                )

    def _validate_cache_source(self, cache_name, source_name):
        source_name, layers = self._split_tagged_source(source_name)
        if self.sources_conf and source_name in self.sources_conf:
            source = self.sources_conf.get(source_name)
            if (
                layers is not None and
                source.get('type') not in TAGGED_SOURCE_TYPES
            ):
                self.errors.append(
                    "Found tagged source '%s' in cache '%s' but tagged sources only "
                    "supported for '%s' sources" % (
                        source_name,
                        cache_name,
                        ', '.join(TAGGED_SOURCE_TYPES)
                    )
                )
                return
            self._validate_source(source_name, source, layers)
            return
        if self.caches_conf and source_name in self.caches_conf:
            self._validate_cache(source_name, self.caches_conf[source_name])
            return
        self.errors.append(
            "Source '%s' for cache '%s' not found in config" % (
                source_name,
                cache_name
            )
        )

    def _validate_bands(self, cache_name, bands):
        if 'l' in bands and len(bands) > 1:
            self.errors.append(
                "Cannot combine 'l' band with bands in cache '%s'" % (
                    cache_name
                )
            )


def validate_options(conf_dict):
    """
    Validate `conf_dict` agains mapproxy.yaml spec.
    Returns tuple with a list of errors and a bool.
    The list is empty when no errors where found.
    The bool is True when the errors are informal and not critical.
    """
    try:
        validate(mapproxy_yaml_spec, conf_dict)
    except ValidationError as ex:
        return ex.errors, ex.informal_only
    else:
        return [], True

coverage = {
    'polygons': str(),
    'polygons_srs': str(),
    'bbox': one_of(str(), [number()]),
    'bbox_srs': str(),
    'ogr_datasource': str(),
    'ogr_where': str(),
    'ogr_srs': str(),
    'datasource': one_of(str(), [number()]),
    'where': str(),
    'srs': str(),
}
image_opts = {
    'mode': str(),
    'colors': number(),
    'transparent': bool(),
    'resampling_method': str(),
    'format': str(),
    'encoding_options': {
        anything(): anything()
    },
    'merge_method': str(),
}

http_opts = {
    'method': str(),
    'client_timeout': number(),
    'ssl_no_cert_checks': bool(),
    'ssl_ca_certs': str(),
    'headers': {
        anything(): str()
    },
}

mapserver_opts = {
    'binary': str(),
    'working_dir': str(),
}

scale_hints = {
    'max_scale': number(),
    'min_scale': number(),
    'max_res': number(),
    'min_res': number(),
}

source_commons = combined(
    scale_hints,
    {
        'concurrent_requests': int(),
        'coverage': coverage,
        'seed_only': bool(),
    }
)

riak_node = {
    'host': str(),
    'pb_port': number(),
    'http_port': number(),
}

cache_types = {
    'file': {
        'directory_layout': str(),
        'use_grid_names': bool(),
        'directory': str(),
        'tile_lock_dir': str(),
    },
    'sqlite': {
        'directory': str(),
        'tile_lock_dir': str(),
    },
    'mbtiles': {
        'filename': str(),
        'tile_lock_dir': str(),
    },
    'couchdb': {
        'url': str(),
        'db_name': str(),
        'tile_metadata': {
            anything(): anything()
        },
        'tile_id': str(),
        'tile_lock_dir': str(),
    },
    'riak': {
        'nodes': [riak_node],
        'protocol': one_of('pbc', 'http', 'https'),
        'bucket': str(),
        'default_ports': {
            'pb': number(),
            'http': number(),
        },
        'secondary_index': bool(),
    }
}

on_error = {
    anything(): {
        required('response'): one_of([int], str),
        'cache': bool,
    }
}



inspire_md = {
    'linked': {
        required('metadata_url'): {
            required('url'): str,
            required('media_type'): str,
        },
        required('languages'): {
            required('default'): str,
        },
    },
    'embedded': {
        required('resource_locators'): [{
            required('url'): str,
            required('media_type'): str,
        }],
        required('temporal_reference'): {
            'date_of_publication': one_of(str, datetime.date),
            'date_of_creation': one_of(str, datetime.date),
            'date_of_last_revision': one_of(str, datetime.date),
        },
        required('conformities'): [{
            'title': string_type,
            'uris': [str],
            'date_of_publication': one_of(str, datetime.date),
            'date_of_creation': one_of(str, datetime.date),
            'date_of_last_revision': one_of(str, datetime.date),
            required('resource_locators'): [{
                required('url'): str,
                required('media_type'): str,
            }],
            required('degree'): str,
        }],
        required('metadata_points_of_contact'): [{
            'organisation_name': string_type,
            'email': str,
        }],
        required('mandatory_keywords'): [str],
        'keywords': [{
            required('title'): string_type,
            'date_of_publication': one_of(str, datetime.date),
            'date_of_creation': one_of(str, datetime.date),
            'date_of_last_revision': one_of(str, datetime.date),
            'uris': [str],
            'resource_locators': [{
                required('url'): str,
                required('media_type'): str,
            }],
            required('keyword_value'): string_type,
        }],
        required('metadata_date'): one_of(str, datetime.date),
        'metadata_url': {
            required('url'): str,
            required('media_type'): str,
        },
        required('languages'): {
            required('default'): str,
        },
    },
}

wms_130_layer_md = {
    'abstract': string_type,
    'keyword_list': [
        {
            'vocabulary': string_type,
            'keywords': [string_type],
        }
    ],
    'attribution': {
        'title': string_type,
        'url':    str,
        'logo': {
            'url':    str,
            'width':  int,
            'height': int,
            'format': string_type,
       }
    },
    'identifier': [
        {
            'url': str,
            'name': string_type,
            'value': string_type,
        }
    ],
    'metadata': [
        {
            'url': str,
            'type': str,
            'format': str,
        },
    ],
    'data': [
        {
            'url': str,
            'format': str,
        }

    ],
    'feature_list': [
        {
            'url': str,
            'format': str,
        }
    ],
}

grid_opts = {
    'base': str(),
    'name': str(),
    'srs': str(),
    'bbox': one_of(str(), [number()]),
    'bbox_srs': str(),
    'num_levels': int(),
    'res': [number()],
    'res_factor': one_of(number(), str()),
    'max_res': number(),
    'min_res': number(),
    'stretch_factor': number(),
    'max_shrink_factor': number(),
    'align_resolutions_with': str(),
    'origin': str(),
    'tile_size': [int()],
    'threshold_res': [number()],
}

ogc_service_md = {
    'title': string_type,
    'abstract': string_type,
    'online_resource': string_type,
    'contact': anything(),
    'fees': string_type,
    'access_constraints': string_type,
    'keyword_list': [
        {
            'vocabulary': string_type,
            'keywords': [string_type],
        }
    ],
}

band_source = {
    required('source'): str(),
    required('band'): int,
    'factor': number(),
}

band_sources = {
    'r': [band_source],
    'g': [band_source],
    'b': [band_source],
    'a': [band_source],
    'l': [band_source],
}

mapproxy_yaml_spec = {
    '__config_files__': anything(), # only used internaly
    'globals': {
        'image': {
            'resampling_method': 'method',
            'paletted': bool(),
            'stretch_factor': number(),
            'max_shrink_factor': number(),
            'jpeg_quality': number(),
            'formats': {
                anything(): image_opts,
            },
            'font_dir': str(),
            'merge_method': str(),
        },
        'http': combined(
            http_opts,
            {
                'access_control_allow_origin': one_of(str(), {}),
            }
        ),
        'cache': {
            'base_dir': str(),
            'lock_dir': str(),
            'tile_lock_dir': str(),
            'meta_size': [number()],
            'meta_buffer': number(),
            'max_tile_limit': number(),
            'minimize_meta_requests': bool(),
            'concurrent_tile_creators': int(),
            'link_single_color_images': bool(),
        },
        'grid': {
            'tile_size': [int()],
        },
        'srs': {
          'axis_order_ne': [str()],
          'axis_order_en': [str()],
          'proj_data_dir': str(),
        },
        'tiles': {
            'expires_hours': number(),
        },
        'mapserver': mapserver_opts,
        'renderd': {
            'address': str(),
        }
    },
    'grids': {
        anything(): grid_opts,
    },
    'caches': {
        anything(): {
            required('sources'): one_of([string_type], band_sources),
            'name': str(),
            'grids': [str()],
            'cache_dir': str(),
            'meta_size': [number()],
            'meta_buffer': number(),
            'minimize_meta_requests': bool(),
            'concurrent_tile_creators': int(),
            'disable_storage': bool(),
            'format': str(),
            'image': image_opts,
            'request_format': str(),
            'use_direct_from_level': number(),
            'use_direct_from_res': number(),
            'link_single_color_images': bool(),
            'watermark': {
                'text': string_type,
                'font_size': number(),
                'color': one_of(str(), [number()]),
                'opacity': number(),
                'spacing': str(),
            },
            'cache': type_spec('type', cache_types)
        }
    },
    'services': {
        'demo': {},
        'kml': {
            'use_grid_names': bool(),
        },
        'tms': {
            'use_grid_names': bool(),
            'origin': str(),
        },
        'wmts': {
            'kvp': bool(),
            'restful': bool(),
            'restful_template': str(),
            'md': ogc_service_md,
        },
        'wms': {
            'srs': [str()],
            'bbox_srs': [one_of(str(), {'bbox': [number()], 'srs': str()})],
            'image_formats': [str()],
            'attribution': {
                'text': string_type,
            },
            'featureinfo_types': [str()],
            'featureinfo_xslt': {
                anything(): str()
            },
            'on_source_errors': str(),
            'max_output_pixels': one_of(number(), [number()]),
            'strict': bool(),
            'md': ogc_service_md,
            'inspire_md': type_spec('type', inspire_md),
            'versions': [str()],
        },
    },

    'sources': {
        anything(): type_spec('type', {
            'wms': combined(source_commons, {
                'wms_opts': {
                    'version': str(),
                    'map': bool(),
                    'featureinfo': bool(),
                    'legendgraphic': bool(),
                    'legendurl': str(),
                    'featureinfo_format': str(),
                    'featureinfo_xslt': str(),
                },
                'image': combined(image_opts, {
                    'opacity':number(),
                    'transparent_color': one_of(str(), [number()]),
                    'transparent_color_tolerance': number(),
                }),
                'supported_formats': [str()],
                'supported_srs': [str()],
                'http': http_opts,
                'forward_req_params': [str()],
                required('req'): {
                    required('url'): str(),
                    anything(): anything()
                }
            }),
            'mapserver': combined(source_commons, {
                    'wms_opts': {
                        'version': str(),
                        'map': bool(),
                        'featureinfo': bool(),
                        'legendgraphic': bool(),
                        'legendurl': str(),
                        'featureinfo_format': str(),
                        'featureinfo_xslt': str(),
                    },
                    'image': combined(image_opts, {
                        'opacity':number(),
                        'transparent_color': one_of(str(), [number()]),
                        'transparent_color_tolerance': number(),
                    }),
                    'supported_formats': [str()],
                    'supported_srs': [str()],
                    'forward_req_params': [str()],
                    required('req'): {
                        required('map'): str(),
                        anything(): anything()
                    },
                    'mapserver': mapserver_opts,
            }),
            'tile': combined(source_commons, {
                required('url'): str(),
                'transparent': bool(),
                'image': image_opts,
                'grid': str(),
                'request_format': str(),
                'origin': str(), # TODO: remove with 1.5
                'http': http_opts,
                'on_error': on_error,
            }),
            'mapnik': combined(source_commons, {
                required('mapfile'): str(),
                'transparent': bool(),
                'image': image_opts,
                'layers': one_of(str(), [str()]),
                'use_mapnik2': bool(),
                'scale_factor': number(),
            }),
            'arcgis': combined(source_commons, {
               required('req'): {
                    required('url'): str(),
                    'dpi': int(),
                    'layers': str(),
                    'transparent': bool(),
                    'time': str()
                },
                'supported_srs': [str()],
                'http': http_opts
            }),
            'debug': {
            },
        })
    },

    'layers': one_of(
        {
            anything(): combined(scale_hints, {
                'sources': [string_type],
                required('title'): string_type,
                'legendurl': str(),
                'md': wms_130_layer_md,
            })
        },
        recursive([combined(scale_hints, {
            'sources': [string_type],
            'tile_sources': [string_type],
            'name': str(),
            required('title'): string_type,
            'legendurl': str(),
            'layers': recursive(),
            'md': wms_130_layer_md,
            'dimensions': {
                anything(): {
                    required('values'): [one_of(string_type, float, int)],
                    'default': one_of(string_type, float, int),
                }
            }
        })])
    ),
     # `parts` can be used for partial configurations that are referenced
     # from other sections (e.g. coverages, dimensions, etc.)
    'parts': anything(),
}
