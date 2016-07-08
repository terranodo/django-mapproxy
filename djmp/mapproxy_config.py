import json
import os
import base64


services_conf = {
    'wms': {'image_formats': ['image/png'],
          'md': {'abstract': 'This is the Harvard HyperMap Proxy.',
                 'title': 'Harvard HyperMap Proxy'},
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

layers_conf = [{
    "name": "",
    "title": "",
    "sources":[
        "tileset_cache"
    ]
}]

caches_conf = {
    "tileset_cache":{
        "grids":[
            "EPSG3857"
        ],
        "sources":[
            "tileset_source"
        ],
        "cache": {}
    }
}

sources_conf = {
    "tileset_source":{
        "type": ""
    }
}

grids_conf = {
    "EPSG3857": {
        "origin": "nw",
        "srs": "EPSG:3857"
    }
}


seed_coverages_conf = {
    "tileset_geom": {
        "bbox": [],
        "srs": "EPSG:3857"
    }
}

seed_seeds_conf = {
    "tileset_seed": {
        "refresh_before": {
            "minutes": 0
        },
        "caches": [
            "tileset_cache"
        ],
        "levels": {
            "from": 0,
            "to": 12
        },
        "coverages": ["tileset_geom"]
    }
}


def get_mapproxy_conf(tileset):

    # cache
    caches_conf['tileset_cache']['cache']['type'] = tileset.cache_type

    if tileset.cache_type == 'file':
        caches_conf['tileset_cache']['cache']['directory'] = os.path.join(tileset.directory, tileset.name)
        caches_conf['tileset_cache']['cache']['directory_layout'] = tileset.directory_layout
    if tileset.cache_type == 'gpkg':
        caches_conf['tileset_cache']['cache']['filename'] = tileset.filename
        caches_conf['tileset_cache']['cache']['table_name'] = tileset.table_name

    # source
    source_type = tileset.source_type

    sources_conf['tileset_source']['type'] = u_to_str(source_type)

    if source_type == 'mapnik':
        sources_conf['tileset_source']['mapfile'] = tileset.mapfile.path 
        sources_conf['tileset_source']['layers'] = [u_to_str(tileset.name)]
        sources_conf['tileset_source']['transparent'] = True
        sources_conf['tileset_source']['coverage'] = {}
        sources_conf['tileset_source']['coverage']['bbox'] = tileset.bbox_3857()
        sources_conf['tileset_source']['coverage']['srs'] = 'EPSG:3857'

    elif source_type == 'wms':
        sources_conf['tileset_source']['req'] = {}
        sources_conf['tileset_source']['req']['url'] = u_to_str(tileset.server_url)
        sources_conf['tileset_source']['req']['layers'] = u_to_str(tileset.layer_name)
        sources_conf['tileset_source']['req']['transparent'] = 'true'

    elif source_type == 'tile':
        sources_conf['sources']['tileset_source']['url'] = u_to_str(tileset.server_url)

    if tileset.server_username and tileset.server_password:
        encoded = base64.b64encode('{}:{}'.format(tileset.server_username, tileset.server_password))
        sources_conf['tileset_source']['http'] = {}
        sources_conf['tileset_source']['http']['headers'] = {}
        sources_conf['tileset_source']['http']['headers']['Authorization'] = 'Basic {}'.format(encoded)
        sources_conf['tileset_source']['http']['ssl_no_cert_checks'] = True

    # layers
    layers_conf[0]['name'] = u_to_str(tileset.name)
    layers_conf[0]['title'] = u_to_str(tileset.name)

    return json.dumps({
            'services': services_conf,
            'layers': layers_conf,
            'caches': caches_conf,
            'sources': sources_conf,
            'grids': grids_conf,
            'globals': {
                "image": {
                    "paletted": False
                },
                'http': {'ssl_no_cert_checks': True},
            }
        })

def get_seed_conf(tileset):

    seed_conf = {
        'coverages': seed_coverages_conf,
        'seeds': seed_seeds_conf
    }

    if tileset.layer_zoom_start > tileset.layer_zoom_stop:
        raise ConfigurationError('invalid configuration - zoom start is greater than zoom stop')
    seed_conf['seeds']['tileset_seed']['levels']['from'] = tileset.layer_zoom_start
    seed_conf['seeds']['tileset_seed']['levels']['to'] = tileset.layer_zoom_stop

    seed_conf['coverages']['tileset_geom']['bbox'] = tileset.bbox_3857()
    
    return json.dumps(seed_conf)



def u_to_str(string):
    return string.encode('ascii', 'ignore')
