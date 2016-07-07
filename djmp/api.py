from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization

from .models import Tileset


class TilesetResource(ModelResource):
    """Tileset API Resource"""


    class Meta:
        queryset = Tileset.objects.all()
        allowed_methods = ['get', 'post', 'put', 'delete']
        resource_name = 'tilesets'
        authorization = DjangoAuthorization()
        always_return_data = True
