import json

from .settings import CACHE_CONFIG

mapproxy_conf = """
    {"services":{
        "wms":{
          "on_source_errors":"raise",
          "image_formats": ["image/png"]
        }
      },
      "layers":[
        {
          "name": "%s",
          "sources":[
            "tileset_cache"
          ]
        }
      ],
      "caches":{
        "tileset_cache":{
          "grids":[
            "EPSG3857"
          ],
          "sources":[
            "tileset_source"
          ],
          "cache":""" + json.dumps(CACHE_CONFIG) +"""
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
      }
    }
    """

seed_conf = """
    {
      "coverages": {
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
      }
    }
    """

def get_mapproxy_conf(layer_name, tileset_source_type):
  return mapproxy_conf % (layer_name, tileset_source_type)

def get_seed_conf(bbox, zoom_start, zoom_stop):
  return seed_conf % (bbox, zoom_start, zoom_stop)