import json
import os
import base64

def wms_source(tileset):
    http = {}
    if tileset.server_username and tileset.server_password:
        encoded = base64.b64encode('{}:{}'.format(tileset.server_username, tileset.server_password))
        http = {
            "headers":{
                "Authorization": 'Basic {}'.format(encoded)
            },
            "ssl_no_cert_checks": True
        }

    return {
        "type": "wms",
        "req": {
            "url": u_to_str(tileset.server_url),
            "layers": u_to_str(tileset.layer_name),
            "transparent": True
        },
        "http": http,
        'coverage': get_coverage(tileset)
    }

def mapnik_source(tileset):
    return {
        "type": "mapnik",
        "mapfile": tileset.mapfile.path,
        "layers": [u_to_str(tileset.name)],
        "transparent": True,
        "coverage": get_coverage(tileset)

    }

def tile_source(tileset):
    return {
        "type": "tile",
        "url": u_to_str(tileset.server_url)
    }

def file_cache(tileset):
    return {
        "type": "file",
        "directory": os.path.join(tileset.directory, str(tileset.id)),
        "directory_layout": tileset.directory_layout
    }

def gpkg_cache(tileset):
    return {
        "type": "gpkg",
        "filename": tileset.filename,
        "table_name": tileset.table_name
    }

def get_coverage(tileset):
    return {
        "bbox": tileset.bbox_3857(),
        "srs": "EPSG:3857"
    }

def seed_seeds(tileset):
    if tileset.layer_zoom_start > tileset.layer_zoom_stop:
        raise ConfigurationError('invalid configuration - zoom start is greater than zoom stop')
    return {
        "refresh_before": {
            "minutes": 0
        },
        "caches": [
            "tileset_cache"
        ],
        "levels": {
            "from": tileset.layer_zoom_start,
            "to": tileset.layer_zoom_stop
        },
        "coverages": ["tileset_geom"]
    }

services_conf = {
    'wms': {'image_formats': ['image/png'],
          'md': {'abstract': 'Djmp',
                 'title': 'Djmp'},
          'srs': ['EPSG:4326', 'EPSG:3857'],
          'versions': ['1.1.1']},
    'wmts': {
          'restful': True,
          'restful_template':
          '/{Layer}/{TileMatrixSet}/{TileMatrix}/{TileCol}/{TileRow}.png',
          },
    'tms': {
          'origin': 'nw',
          },
    'demo': None
}

def grids_conf():
    return {
        "EPSG3857": {
            "origin": "nw",
            "srs": "EPSG:3857",
            "num_levels": 30
        },
        "EPSG4326": {
            "origin": "nw",
            "srs": "EPSG:4326",
            "num_levels": 30
        }
    }

sources_conf = {
    "wms": wms_source,
    "mapnik": mapnik_source,
    "tile": tile_source
}

cache_conf = {
    "file": file_cache,
    "gpkg": gpkg_cache
}


def get_mapproxy_conf(tileset):
    return json.dumps({
        'services': services_conf,
        'layers':  [{
            "name": u_to_str(tileset.name),
            "title": u_to_str(tileset.name),
            "sources":[
                "tileset_cache"
            ]
        }],
        'caches': {
            "tileset_cache":{
                "grids":[
                    "EPSG3857"
                ],
                "sources":[
                    "tileset_source"
                ],
                "cache": cache_conf.get(tileset.cache_type)(tileset)
            }
        },
        'sources': {
            'tileset_source': sources_conf.get(tileset.source_type)(tileset)
        },  
        'grids': grids_conf(),
        'globals': {
            "image": {
                "paletted": False
            },
            'http': {'ssl_no_cert_checks': True},
        }
    })

def get_seed_conf(tileset):

    seed_conf = {
        'coverages': {
            "tileset_geom": get_coverage(tileset)
        },
        'seeds': {
            "tileset_seed": seed_seeds(tileset)
        }
    }
    
    return json.dumps(seed_conf)

def u_to_str(string):
    return string.encode('ascii', 'ignore')
