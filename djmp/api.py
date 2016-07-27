import importlib

from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource

from .models import Tileset

from .settings import DJMP_AUTHORIZATION_CLASS

module_name, class_name = DJMP_AUTHORIZATION_CLASS.rsplit(".", 1)
auth_class = getattr(importlib.import_module(module_name), class_name)


class TilesetResource(ModelResource):
    """Tileset API Resource"""

    class Meta:
        queryset = Tileset.objects.all()
        allowed_methods = ['get', 'post', 'put', 'delete']
        resource_name = 'tilesets'
        authorization = auth_class()
        always_return_data = True
