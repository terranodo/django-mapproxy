from tastypie.constants import ALL, ALL_WITH_RELATIONS
from tastypie.resources import ModelResource
from tastypie.authorization import DjangoAuthorization

from .guardian_auth import GuardianAuthorization
from .models import Tileset


class TilesetResource(ModelResource):
    """Tileset API Resource"""

    class Meta:
        queryset = Tileset.objects.all()
        allowed_methods = ['get', 'post', 'put', 'delete']
        resource_name = 'tilesets'
        authorization = GuardianAuthorization()
        always_return_data = True
