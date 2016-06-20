import json
import os

from pyproj import Proj, transform

mapproxy_conf = """
    {"services":{
        "wms":{
            "on_source_errors":"raise",
            "image_formats": ["image/png"]
        }
    },
    "layers":[{
        "name": "%s",
        "title": "%s",
        "sources":[
            "tileset_cache"
        ]}
    ],
    "caches":{
        "tileset_cache":{
        "grids":[
            "EPSG3857"
        ],
        "sources":[
            "tileset_source"
        ],
        "cache": %s
        }
    },
    "sources":{
        "tileset_source":{
        "type": "%s"
    }
    },
    "grids":{
        "EPSG3857": {
            "origin": "nw",
            "srs": "EPSG:3857"
        }
    },
    "globals": {
        "image": {
        "paletted": false
        }
    }}
"""

seed_conf = """
    {"coverages": {
        "tileset_geom": {
            "bbox": %s,
            "srs": "EPSG:3857"
        }
    },
    "seeds": {
        "tileset_seed": {
            "refresh_before": {
                "minutes": 0
            },
            "caches": [
                "tileset_cache"
            ],
            "levels": {
                "from": %s,
                "to": %s
            },
            "coverages": ["tileset_geom"]
        }
    }}
    """

def get_mapproxy_conf(tileset):

    cache_conf = {
        'type': tileset.cache_type
    }
    if tileset.cache_type == 'file':
        cache_conf['directory'] = os.path.join(tileset.directory, tileset.name)
        cache_conf['directory_layout'] = tileset.directory_layout
    if tileset.cache_type == 'gpkg':
        cache_conf['filename'] = tileset.filename
        cache_conf['table_name'] = tileset.table_name

    return mapproxy_conf % (
        u_to_str(tileset.layer_name),
        u_to_str(tileset.layer_name),
        json.dumps(cache_conf),
        u_to_str(tileset.server_service_type)
        )

def get_seed_conf(tileset):
    bbox = bbox_to_3857(tileset.bbox_x0, tileset.bbox_y0, tileset.bbox_x1, tileset.bbox_y1)
    return seed_conf % (bbox, tileset.layer_zoom_start, tileset.layer_zoom_stop)


def bbox_to_3857(bbox_x0, bbox_y0, bbox_x1, bbox_y1):
    inProj = Proj(init='epsg:4326')
    outProj = Proj(init='epsg:3857')

    sw = transform(inProj, outProj, bbox_x0, bbox_y0)
    ne = transform(inProj, outProj, bbox_x1, bbox_y1)

    return [sw[0], sw[1], ne[0], ne[1]]

def u_to_str(string):
    return string.encode('ascii', 'ignore')
