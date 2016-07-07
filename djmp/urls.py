from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin

from tastypie.api import Api

from .views import DetailView, seed, tileset_status, tileset_mapproxy
from .api import TilesetResource

admin.autodiscover()

api = Api(api_name='api')
api.register(TilesetResource())

urlpatterns = patterns('',
    url(r'^(?P<pk>\d+)/$', DetailView.as_view(), name='tileset_detail'),
    url(r'^(?P<pk>\d+)/seed$', seed, name='tileset_seed'),
    url(r'^(?P<pk>\d+)/status$', tileset_status, name='tileset_status'),
    url(r'^(?P<pk>\d+)/map(?P<path_info>/.*)$', tileset_mapproxy, name='tileset_mapproxy'),
    (r'^admin/', include(admin.site.urls)),
    url(r'', include(api.urls)),
)
