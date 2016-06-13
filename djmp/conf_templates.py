import json

from django.conf import settings

mapproxy_conf = """
    {
      "services":{
        "wms":{
          "on_source_errors":"raise",
          "image_formats": ["image/png"]
        }
      },
      "layers":[
        {
          "name":"{layer_name}",
          "title":"{layer_title}",
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
          "cache":""" + json.loads(settings.CACHE_CONFIG) +"""
        }
      },
      "sources":{
        "tileset_source":{
          "type": {tileset_source_type}
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
          "bbox": {seed_bbox},
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
            "from": {seed_zoom_start},
            "to": {seed_zoom_end}
          },
          "coverages": ["tileset_geom"]
        }
      }
    }
    """
