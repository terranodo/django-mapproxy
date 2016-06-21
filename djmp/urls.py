from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin

from .views import DetailView, seed, tileset_status

admin.autodiscover()

urlpatterns = patterns('',

    url(r'^(?P<pk>\d+)/$', DetailView.as_view(), name='tileset_detail'),
    url(r'^(?P<pk>\d+)/seed$', seed, name='tileset_seed'),
    url(r'^(?P<pk>\d+)/status$', tileset_status, name='tileset_status'),
    (r'^admin/', include(admin.site.urls)),
)
